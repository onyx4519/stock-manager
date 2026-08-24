from datetime import datetime

from pydantic import BaseModel, Field


class NewsArticle(BaseModel):
    id: str
    title: str
    author: str | None = None
    description: str | None = None
    article_url: str
    image_url: str | None = None
    publisher_name: str
    publisher_homepage_url: str | None = None
    published_at: datetime
    tickers: list[str]
    provider: str = "Massive"


class NewsFeed(BaseModel):
    symbols: list[str]
    items: list[NewsArticle]
    total_count: int = Field(ge=0)
