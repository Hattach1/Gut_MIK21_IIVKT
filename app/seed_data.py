from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import Game

Base.metadata.create_all(bind=engine)


TEST_GAMES = [
    {
        "steam_app_id": 1245620,
        "name": "ELDEN RING",
        "genres": "Action RPG, Open World",
        "tags": "souls-like, fantasy, difficult, dark fantasy, exploration",
        "short_description": "An action RPG set in a vast dark fantasy open world with challenging combat and deep exploration.",
        "rating": 9.6,
        "num_reviews": 650000,
        "image_url": ""
    },
    {
        "steam_app_id": 292030,
        "name": "The Witcher 3: Wild Hunt",
        "genres": "RPG, Open World",
        "tags": "story rich, fantasy, choices, adventure, open world",
        "short_description": "A story-driven open world RPG where players hunt monsters, make choices, and explore a fantasy world.",
        "rating": 9.7,
        "num_reviews": 900000,
        "image_url": ""
    },
    {
        "steam_app_id": 489830,
        "name": "The Elder Scrolls V: Skyrim Special Edition",
        "genres": "RPG, Open World",
        "tags": "dragons, fantasy, modding, exploration, open world",
        "short_description": "A fantasy open world RPG with dragons, quests, character progression, and exploration.",
        "rating": 9.1,
        "num_reviews": 540000,
        "image_url": ""
    },
    {
        "steam_app_id": 1174180,
        "name": "Red Dead Redemption 2",
        "genres": "Action, Adventure, Open World",
        "tags": "western, story rich, horses, realistic, open world",
        "short_description": "A cinematic open world western adventure with a rich story, exploration, and immersive realism.",
        "rating": 9.5,
        "num_reviews": 700000,
        "image_url": ""
    },
    {
        "steam_app_id": 1091500,
        "name": "Cyberpunk 2077",
        "genres": "RPG, Open World, Sci-Fi",
        "tags": "cyberpunk, futuristic, story rich, action, rpg",
        "short_description": "A futuristic open world action RPG set in a cyberpunk city full of quests and choices.",
        "rating": 8.6,
        "num_reviews": 800000,
        "image_url": ""
    },
    {
        "steam_app_id": 374320,
        "name": "DARK SOULS III",
        "genres": "Action RPG",
        "tags": "souls-like, difficult, dark fantasy, bosses, atmospheric",
        "short_description": "A dark fantasy action RPG with difficult boss fights, atmospheric locations, and deep combat.",
        "rating": 9.4,
        "num_reviews": 300000,
        "image_url": ""
    },
    {
        "steam_app_id": 271590,
        "name": "Grand Theft Auto V",
        "genres": "Action, Open World",
        "tags": "crime, city, driving, open world, multiplayer",
        "short_description": "An action open world game about crime, missions, vehicles, and life in a massive modern city.",
        "rating": 8.9,
        "num_reviews": 1700000,
        "image_url": ""
    },
    {
        "steam_app_id": 578080,
        "name": "PUBG: BATTLEGROUNDS",
        "genres": "Shooter, Battle Royale, Multiplayer",
        "tags": "battle royale, survival, pvp, shooter, tactical",
        "short_description": "A multiplayer battle royale shooter focused on survival, tactical combat, and player versus player matches.",
        "rating": 7.8,
        "num_reviews": 1400000,
        "image_url": ""
    },
    {
        "steam_app_id": 730,
        "name": "Counter-Strike 2",
        "genres": "Shooter, Multiplayer",
        "tags": "fps, tactical, competitive, esports, team-based",
        "short_description": "A tactical competitive first-person shooter focused on team play, precise aim, and esports gameplay.",
        "rating": 8.4,
        "num_reviews": 6000000,
        "image_url": ""
    },
    {
        "steam_app_id": 570,
        "name": "Dota 2",
        "genres": "MOBA, Strategy, Multiplayer",
        "tags": "moba, competitive, team-based, esports, strategy",
        "short_description": "A highly competitive multiplayer online battle arena game with strategic team-based matches.",
        "rating": 8.8,
        "num_reviews": 2000000,
        "image_url": ""
    },
    {
        "steam_app_id": 413150,
        "name": "Stardew Valley",
        "genres": "Simulation, RPG, Indie",
        "tags": "farming, relaxing, pixel graphics, cozy, crafting",
        "short_description": "A relaxing farming and life simulation game with crafting, exploration, and charming pixel visuals.",
        "rating": 9.8,
        "num_reviews": 750000,
        "image_url": ""
    },
    {
        "steam_app_id": 646570,
        "name": "Slay the Spire",
        "genres": "Roguelike, Card Game, Strategy, Indie",
        "tags": "deckbuilding, roguelike, cards, strategy, replayability",
        "short_description": "A roguelike deckbuilding game where players build card combinations and battle through repeated runs.",
        "rating": 9.5,
        "num_reviews": 150000,
        "image_url": ""
    }
]


def seed_games():
    db: Session = SessionLocal()
    try:
        existing_count = db.query(Game).count()
        if existing_count > 0:
            print("Database already contains games. Skipping seed.")
            return

        for game_data in TEST_GAMES:
            game = Game(**game_data)
            db.add(game)

        db.commit()
        print("Test games added successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_games()