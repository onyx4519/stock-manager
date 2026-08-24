from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import dart, market, portfolio, stocks
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market.router, prefix=settings.api_prefix)
app.include_router(stocks.router, prefix=settings.api_prefix)
app.include_router(portfolio.router, prefix=settings.api_prefix)
app.include_router(dart.router, prefix=settings.api_prefix)


@app.get("/health")
def health():
    return {"status": "ok", "mock_mode": settings.mock_mode}
