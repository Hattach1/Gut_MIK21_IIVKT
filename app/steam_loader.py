import os
import time
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.models import Game

load_dotenv()

STEAM_API_KEY = os.getenv("STEAM_API_KEY")

STEAM_APP_LIST_URL = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
STEAM_APP_DETAILS_URL = "https://store.steampowered.com/api/appdetails"


def fetch_app_list(limit: int = 100) -> List[Dict]:
    if not STEAM_API_KEY:
        raise ValueError("Steam API key not found in .env")

    apps: List[Dict] = []
    last_appid = 0

    while len(apps) < limit:
        response = requests.get(
            STEAM_APP_LIST_URL,
            params={
                "key": STEAM_API_KEY,
                "max_results": 5000,
                "last_appid": last_appid,
            },
            timeout=20,
        )
        response.raise_for_status()

        data = response.json().get("response", {})
        new_apps = data.get("apps", [])

        if not new_apps:
            break

        apps.extend(new_apps)
        last_appid = data.get("last_appid", last_appid)

    return apps[:limit]


def fetch_app_details(appid: int) -> Dict:
    try:
        response = requests.get(
            STEAM_APP_DETAILS_URL,
            params={"appids": appid, "l": "english"},
            timeout=15,
        )
        response.raise_for_status()

        data = response.json()
        app_data = data.get(str(appid), {})

        if not app_data.get("success"):
            return {}

        return app_data.get("data", {})
    except Exception:
        return {}


def fetch_reviews_summary(appid: int, num_per_page: int = 100) -> Dict:
    url = f"https://store.steampowered.com/appreviews/{appid}"

    try:
        response = requests.get(
            url,
            params={
                "json": 1,
                "language": "all",
                "filter": "recent",
                "num_per_page": num_per_page,
                "purchase_type": "all",
                "cursor": "*",
            },
            timeout=20,
        )
        response.raise_for_status()

        data = response.json()
        reviews = data.get("reviews", [])
        query_summary = data.get("query_summary", {})

        total_reviews = (
            query_summary.get("total_reviews")
            or query_summary.get("total_positive")
            or len(reviews)
        )

        if not reviews:
            return {
                "num_reviews": int(total_reviews) if total_reviews else 0,
                "positive_ratio": 0.0,
                "rating": 0.0,
            }

        positive_count = 0
        for review in reviews:
            if review.get("voted_up") is True:
                positive_count += 1

        sample_count = len(reviews)
        positive_ratio = positive_count / sample_count
        rating = round(positive_ratio * 10, 2)

        return {
            "num_reviews": int(total_reviews) if total_reviews else sample_count,
            "positive_ratio": positive_ratio,
            "rating": rating,
        }

    except Exception:
        return {
            "num_reviews": 0,
            "positive_ratio": 0.0,
            "rating": 0.0,
        }


def is_probably_valid_game(details: Dict) -> bool:
    if not details:
        return False

    if details.get("type") != "game":
        return False

    name = (details.get("name") or "").strip().lower()
    short_description = (details.get("short_description") or "").strip().lower()
    genres = details.get("genres", [])
    categories = details.get("categories", [])

    if not name:
        return False

    if not short_description or len(short_description) < 30:
        return False

    if not genres:
        return False

    banned_name_words = [
        "demo",
        "soundtrack",
        "ost",
        "dlc",
        "expansion pass",
        "season pass",
        "playtest",
        "dedicated server",
        "server",
        "editor",
        "sdk",
        "tool",
        "benchmark",
        "test server",
    ]

    for word in banned_name_words:
        if word in name:
            return False

    category_names = [c.get("description", "").lower() for c in categories if c.get("description")]

    for cat in category_names:
        if "downloadable content" in cat:
            return False

    # Можно оставить проверку картинки выключенной, чтобы не отбрасывать лишние игры
    # if not details.get("header_image"):
    #     return False

    required_age = details.get("required_age", 0)
    try:
        if int(required_age) >= 18:
            return False
    except Exception:
        pass

    return True


def parse_game_data(appid: int, details: Dict, reviews_summary: Optional[Dict] = None) -> Dict:
    name = details.get("name", "")

    genres = ""
    if "genres" in details:
        genres = ", ".join(
            [g.get("description", "") for g in details["genres"] if g.get("description")]
        )

    categories = ""
    if "categories" in details:
        categories = ", ".join(
            [c.get("description", "") for c in details["categories"] if c.get("description")]
        )

    description = details.get("short_description", "")

    rating = None
    num_reviews = None

    if reviews_summary:
        rating = reviews_summary.get("rating")
        num_reviews = reviews_summary.get("num_reviews")

    return {
        "steam_app_id": appid,
        "name": name,
        "genres": genres,
        "tags": categories,
        "short_description": description,
        "rating": rating,
        "num_reviews": num_reviews,
        "image_url": None,  # намеренно не сохраняем картинку
    }


def process_single_app(app: Dict) -> Optional[Dict]:
    appid = app.get("appid")
    if not appid:
        return None

    details = fetch_app_details(appid)

    if not is_probably_valid_game(details):
        return None

    game_data = parse_game_data(appid, details, reviews_summary=None)
    return game_data


def load_games_from_steam(
    db: Session,
    target_count: int = 100,
    with_reviews: bool = False,
    max_apps_to_scan: int = 5000,
    max_workers: int = 20,
    batch_size: int = 200,
) -> Dict:
    apps = fetch_app_list(limit=max_apps_to_scan)

    added = 0
    scanned = 0
    skipped_existing = 0
    skipped_invalid = 0

    existing_ids = {
        row[0]
        for row in db.query(Game.steam_app_id).filter(Game.steam_app_id.isnot(None)).all()
    }

    candidate_apps = []
    for app in apps:
        appid = app.get("appid")
        if not appid:
            continue
        if appid in existing_ids:
            skipped_existing += 1
            continue
        candidate_apps.append(app)

    for start in range(0, len(candidate_apps), batch_size):
        if added >= target_count:
            break

        batch = candidate_apps[start:start + batch_size]
        scanned += len(batch)

        valid_game_dicts = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_single_app, app) for app in batch]

            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result is None:
                        skipped_invalid += 1
                        continue
                    valid_game_dicts.append(result)
                except Exception:
                    skipped_invalid += 1

        for game_data in valid_game_dicts:
            if added >= target_count:
                break

            game = Game(**game_data)
            db.add(game)
            added += 1

            if added % 50 == 0:
                db.commit()

        db.commit()

    reviews_updated = 0
    if with_reviews and added > 0:
        new_games = (
            db.query(Game)
            .filter(Game.rating.is_(None))
            .filter(Game.steam_app_id.isnot(None))
            .order_by(Game.id.desc())
            .limit(min(added, 200))
            .all()
        )

        for game in new_games:
            summary = fetch_reviews_summary(game.steam_app_id, num_per_page=100)
            game.rating = summary.get("rating", 0.0)
            game.num_reviews = summary.get("num_reviews", 0)
            reviews_updated += 1

            if reviews_updated % 20 == 0:
                db.commit()

            time.sleep(0.05)

        db.commit()

    return {
        "added": added,
        "scanned": scanned,
        "skipped_existing": skipped_existing,
        "skipped_invalid": skipped_invalid,
        "reviews_updated": reviews_updated,
        "used_parallel_loading": True,
        "max_workers": max_workers,
        "batch_size": batch_size,
    }


def update_reviews_for_existing_games(db: Session, limit: int = 50) -> Dict:
    games = (
        db.query(Game)
        .filter(Game.steam_app_id.isnot(None))
        .limit(limit)
        .all()
    )

    updated = 0

    for game in games:
        summary = fetch_reviews_summary(game.steam_app_id, num_per_page=100)
        game.rating = summary.get("rating", 0.0)
        game.num_reviews = summary.get("num_reviews", 0)
        updated += 1

        if updated % 10 == 0:
            db.commit()

        time.sleep(0.1)

    db.commit()
    return {"updated": updated}