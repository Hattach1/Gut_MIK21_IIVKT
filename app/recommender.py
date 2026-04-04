from typing import List, Optional, Tuple, Set

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.models import Game


IMPORTANT_TAG_KEYWORDS = {
    "souls-like",
    "roguelike",
    "roguelite",
    "metroidvania",
    "deckbuilding",
    "deckbuilder",
    "survival",
    "crafting",
    "sandbox",
    "open world",
    "immersive sim",
    "tactical",
    "turn-based",
    "turn-based strategy",
    "grand strategy",
    "4x",
    "city builder",
    "strategy",
    "moba",
    "battle royale",
    "fps",
    "shooter",
    "horror",
    "survival horror",
    "cozy",
    "farming",
    "simulation",
    "visual novel",
    "platformer",
    "puzzle",
    "action rpg",
    "jrpg",
    "crpg",
    "party-based rpg",
}


def split_to_tokens(text: Optional[str]) -> Set[str]:
    if not text:
        return set()
    return {part.strip().lower() for part in text.split(",") if part.strip()}


def extract_game_tags(game: Game) -> Set[str]:
    genres = split_to_tokens(game.genres)
    tags = split_to_tokens(game.tags)
    return genres.union(tags)


def extract_genres(game: Game) -> Set[str]:
    return split_to_tokens(game.genres)


def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    if not set_a or not set_b:
        return 0.0
    intersection = set_a.intersection(set_b)
    union = set_a.union(set_b)
    if not union:
        return 0.0
    return len(intersection) / len(union)


def important_tag_overlap_score(game_a: Game, game_b: Game) -> float:
    tags_a = extract_game_tags(game_a)
    tags_b = extract_game_tags(game_b)

    overlap = tags_a.intersection(tags_b)

    if not overlap:
        return 0.0

    score = 0.0
    for tag in overlap:
        if tag in IMPORTANT_TAG_KEYWORDS:
            score += 0.15
        else:
            score += 0.04

    return min(score, 0.35)


def genre_overlap_score(game_a: Game, game_b: Game) -> float:
    genres_a = extract_genres(game_a)
    genres_b = extract_genres(game_b)
    return jaccard_similarity(genres_a, genres_b)


def build_game_text(game: Game) -> str:
    """
    Финальное текстовое представление игры.
    Жанры и теги важнее описания.
    """
    name = (game.name or "").lower().strip()
    genres = (game.genres or "").lower().strip()
    tags = (game.tags or "").lower().strip()
    description = (game.short_description or "").lower().strip()

    weighted_text = " ".join([
        name,
        name,
        genres,
        genres,
        genres,
        tags,
        tags,
        tags,
        tags,
        description,
    ])

    return weighted_text


def get_all_games(db: Session) -> List[Game]:
    return db.query(Game).all()


def normalize_rating(rating: Optional[float]) -> float:
    if rating is None:
        return 0.0
    return min(max(rating / 10.0, 0.0), 1.0)


def normalize_popularity(num_reviews: Optional[int]) -> float:
    if not num_reviews or num_reviews <= 0:
        return 0.0
    return min(np.log1p(num_reviews) / np.log1p(10_000_000), 1.0)


def confidence_from_reviews(num_reviews: Optional[int]) -> float:
    if not num_reviews or num_reviews <= 0:
        return 0.0
    return min(np.log1p(num_reviews) / np.log1p(5000), 1.0)


def calculate_final_score(
    similarity_score: float,
    rating: Optional[float],
    num_reviews: Optional[int],
    tag_bonus: float,
    genre_bonus: float,
    genre_penalty: float,
) -> float:
    rating_score = normalize_rating(rating)
    popularity_score = normalize_popularity(num_reviews)
    confidence_score = confidence_from_reviews(num_reviews)
    weighted_rating = rating_score * confidence_score

    final_score = (
        0.72 * similarity_score +
        0.18 * tag_bonus +
        0.08 * genre_bonus +
        0.05 * weighted_rating +
        0.02 * popularity_score -
        0.10 * genre_penalty
    )
    return float(final_score)


def build_tfidf_matrix(games: List[Game]):
    documents = [build_game_text(game) for game in games]
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.80
    )
    tfidf_matrix = vectorizer.fit_transform(documents)
    return vectorizer, tfidf_matrix


def _dense_mean_profile(liked_rows):
    """Sparse .mean(axis=0) returns np.matrix; sklearn rejects it in cosine_similarity."""
    return np.asarray(liked_rows.mean(axis=0), dtype=np.float64).reshape(1, -1)


def _dense_tfidf_row(matrix, row_index: int) -> np.ndarray:
    return np.asarray(matrix[row_index].toarray(), dtype=np.float64)


def is_candidate_relevant(
    similarity_score: float,
    avg_tag_bonus: float,
    avg_genre_bonus: float
) -> bool:
    """
    Жёсткий фильтр кандидатов.
    """
    if similarity_score >= 0.18:
        return True

    if avg_tag_bonus >= 0.12:
        return True

    if avg_genre_bonus >= 0.30 and similarity_score >= 0.10:
        return True

    return False


def recommend_games_by_liked_titles(
    db: Session,
    liked_titles: List[str],
    top_k: int = 5
) -> List[Game]:
    games = get_all_games(db)

    if not games:
        return []

    _, tfidf_matrix = build_tfidf_matrix(games)

    liked_indices = []
    liked_titles_lower = [title.lower().strip() for title in liked_titles]

    for idx, game in enumerate(games):
        if game.name and game.name.lower().strip() in liked_titles_lower:
            liked_indices.append(idx)

    if not liked_indices:
        return []

    liked_vectors = tfidf_matrix[liked_indices]
    user_profile_vector = _dense_mean_profile(liked_vectors)
    similarities = cosine_similarity(user_profile_vector, tfidf_matrix).flatten()

    liked_games = [games[idx] for idx in liked_indices]
    scored_candidates: List[Tuple[int, float]] = []

    for idx, similarity_score in enumerate(similarities):
        candidate_game = games[idx]
        game_name = (candidate_game.name or "").lower().strip()

        if game_name in liked_titles_lower:
            continue

        tag_bonuses = []
        genre_bonuses = []

        for liked_game in liked_games:
            tag_bonuses.append(important_tag_overlap_score(candidate_game, liked_game))
            genre_bonuses.append(genre_overlap_score(candidate_game, liked_game))

        avg_tag_bonus = float(np.mean(tag_bonuses)) if tag_bonuses else 0.0
        avg_genre_bonus = float(np.mean(genre_bonuses)) if genre_bonuses else 0.0

        if not is_candidate_relevant(
            similarity_score=similarity_score,
            avg_tag_bonus=avg_tag_bonus,
            avg_genre_bonus=avg_genre_bonus
        ):
            continue

        genre_penalty = 0.0
        if avg_genre_bonus < 0.12:
            genre_penalty = 0.15

        final_score = calculate_final_score(
            similarity_score=similarity_score,
            rating=candidate_game.rating,
            num_reviews=candidate_game.num_reviews,
            tag_bonus=avg_tag_bonus,
            genre_bonus=avg_genre_bonus,
            genre_penalty=genre_penalty,
        )

        scored_candidates.append((idx, final_score))

    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    recommended_games = [games[idx] for idx, _score in scored_candidates[:top_k]]
    return recommended_games


def get_similar_games(
    db: Session,
    game_title: str,
    top_k: int = 5
) -> List[Game]:
    games = get_all_games(db)

    if not games:
        return []

    _, tfidf_matrix = build_tfidf_matrix(games)

    target_index = None
    target_title_lower = game_title.lower().strip()

    for idx, game in enumerate(games):
        if game.name and game.name.lower().strip() == target_title_lower:
            target_index = idx
            break

    if target_index is None:
        return []

    target_game = games[target_index]
    query_dense = _dense_tfidf_row(tfidf_matrix, target_index)
    similarity_scores = cosine_similarity(query_dense, tfidf_matrix).flatten()

    scored_candidates = []

    for idx, similarity_score in enumerate(similarity_scores):
        if idx == target_index:
            continue

        candidate_game = games[idx]
        tag_bonus = important_tag_overlap_score(target_game, candidate_game)
        genre_bonus = genre_overlap_score(target_game, candidate_game)

        if not is_candidate_relevant(
            similarity_score=similarity_score,
            avg_tag_bonus=tag_bonus,
            avg_genre_bonus=genre_bonus
        ):
            continue

        genre_penalty = 0.0
        if genre_bonus < 0.12:
            genre_penalty = 0.15

        final_score = calculate_final_score(
            similarity_score=similarity_score,
            rating=candidate_game.rating,
            num_reviews=candidate_game.num_reviews,
            tag_bonus=tag_bonus,
            genre_bonus=genre_bonus,
            genre_penalty=genre_penalty,
        )

        scored_candidates.append((idx, final_score))

    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    similar_games = [games[idx] for idx, _score in scored_candidates[:top_k]]
    return similar_games