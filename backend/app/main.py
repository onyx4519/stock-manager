from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import dart, market, portfolio, stocks, transactions
from app.core.config import settings
from app.providers.market import MarketProviderConfigurationError, MarketProviderError

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
app.include_router(transactions.router, prefix=settings.api_prefix)
app.include_router(dart.router, prefix=settings.api_prefix)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "mock_mode": settings.mock_mode,
        "market_provider": settings.market_provider,
    }


@app.exception_handler(MarketProviderConfigurationError)
async def market_provider_configuration_error(
    _request: Request,
    _exc: MarketProviderConfigurationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Market data provider is not configured."},
    )


@app.exception_handler(MarketProviderError)
async def market_provider_error(
    _request: Request,
    _exc: MarketProviderError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "detail": "Market data provider is unavailable or returned invalid data."
        },
    )
