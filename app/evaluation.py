from typing import List, Dict

from app import recommender


def evaluate_recommender_from_likes(
    db,
    liked_titles: List[str],
    top_k: int = 5,
    test_ratio: float = 0.4
) -> Dict:
    """
    Простая offline-оценка:
    - часть liked_titles идёт в train
    - часть в test
    - строим рекомендации по train
    - проверяем, попали ли test игры в рекомендации
    """
    cleaned_titles = [title.strip() for title in liked_titles if title.strip()]

    if len(cleaned_titles) < 3:
        return {
            "error": "Для оценки нужно минимум 3 liked games"
        }

    split_index = max(1, int(len(cleaned_titles) * (1 - test_ratio)))

    train_titles = cleaned_titles[:split_index]
    test_titles = cleaned_titles[split_index:]

    if not test_titles:
        test_titles = [cleaned_titles[-1]]
        train_titles = cleaned_titles[:-1]

    recommendations = recommender.recommend_games_by_liked_titles(
        db=db,
        liked_titles=train_titles,
        top_k=top_k
    )

    recommended_titles = [game.name for game in recommendations]

    hits = 0
    for test_title in test_titles:
        if test_title in recommended_titles:
            hits += 1

    hit_rate = 1.0 if hits > 0 else 0.0
    precision_at_k = hits / top_k if top_k > 0 else 0.0
    recall_at_k = hits / len(test_titles) if test_titles else 0.0

    return {
        "train_titles": train_titles,
        "test_titles": test_titles,
        "recommended_titles": recommended_titles,
        "hits": hits,
        "hit_rate": round(hit_rate, 4),
        "precision_at_k": round(precision_at_k, 4),
        "recall_at_k": round(recall_at_k, 4),
    }