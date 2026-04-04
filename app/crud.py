from sqlalchemy.orm import Session
from app import models, schemas


def create_game(db: Session, game: schemas.GameCreate):
    db_game = models.Game(**game.model_dump())
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game


def get_games(db: Session, skip: int = 0, limit: int = 20):
    return db.query(models.Game).offset(skip).limit(limit).all()


def get_game_by_id(db: Session, game_id: int):
    return db.query(models.Game).filter(models.Game.id == game_id).first()


def search_games_by_name(db: Session, query: str, limit: int = 20):
    return (
        db.query(models.Game)
        .filter(models.Game.name.ilike(f"%{query}%"))
        .limit(limit)
        .all()
    )