from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app import crud, schemas, recommender, steam_loader, evaluation

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Steam Game Recommender API",
    description="API для рекомендательной системы игр на основе данных Steam",
    version="0.1.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/ui", response_class=HTMLResponse)
def ui_page(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/")
def root():
    return {"message": "Steam Game Recommender API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/games", response_model=schemas.GameResponse)
def create_game(game: schemas.GameCreate, db: Session = Depends(get_db)):
    return crud.create_game(db, game)


@app.get("/games", response_model=List[schemas.GameResponse])
def get_games(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return crud.get_games(db, skip=skip, limit=limit)


@app.get("/games/{game_id}", response_model=schemas.GameResponse)
def get_game(game_id: int, db: Session = Depends(get_db)):
    game = crud.get_game_by_id(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@app.get("/games/search/", response_model=List[schemas.GameResponse])
def search_games(query: str, db: Session = Depends(get_db)):
    return crud.search_games_by_name(db, query=query)


@app.post("/recommendations", response_model=List[schemas.GameResponse])
def get_recommendations(
    request: schemas.RecommendationRequest,
    db: Session = Depends(get_db)
):
    recommendations = recommender.recommend_games_by_liked_titles(
        db=db,
        liked_titles=request.liked_titles,
        top_k=request.top_k
    )
    return recommendations


@app.post("/games/similar", response_model=List[schemas.GameResponse])
def get_similar_games(
    request: schemas.SimilarGamesRequest,
    db: Session = Depends(get_db)
):
    similar_games = recommender.get_similar_games(
        db=db,
        game_title=request.title,
        top_k=request.top_k
    )
    return similar_games


@app.post("/admin/load-steam-games")
def load_steam_games(
    target_count: int = 100,
    with_reviews: bool = False,
    max_apps_to_scan: int = 5000,
    max_workers: int = 20,
    batch_size: int = 200,
    db: Session = Depends(get_db)
):
    result = steam_loader.load_games_from_steam(
        db=db,
        target_count=target_count,
        with_reviews=with_reviews,
        max_apps_to_scan=max_apps_to_scan,
        max_workers=max_workers,
        batch_size=batch_size
    )
    return result


@app.post("/admin/update-game-reviews")
def update_game_reviews(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    result = steam_loader.update_reviews_for_existing_games(
        db=db,
        limit=limit
    )
    return result


@app.post("/evaluate/recommender")
def evaluate_recommender(
    request: schemas.EvaluationRequest,
    db: Session = Depends(get_db)
):
    result = evaluation.evaluate_recommender_from_likes(
        db=db,
        liked_titles=request.liked_titles,
        top_k=request.top_k,
        test_ratio=request.test_ratio
    )
    return result