from sqlalchemy import Column, Integer, String, Text, Float
from app.database import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    steam_app_id = Column(Integer, unique=True, index=True, nullable=True)
    name = Column(String, index=True, nullable=False)
    genres = Column(String, nullable=True)
    tags = Column(String, nullable=True)
    short_description = Column(Text, nullable=True)
    rating = Column(Float, nullable=True)
    num_reviews = Column(Integer, nullable=True)
    image_url = Column(String, nullable=True)