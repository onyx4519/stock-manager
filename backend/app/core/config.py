import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


def _read_bool(name: str, *, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(f"{name} must be a boolean value.")


class Settings:
    def __init__(self) -> None:
        self.app_name = os.getenv("APP_NAME", "Stock Manager API")
        self.api_prefix = os.getenv("API_PREFIX", "/api/v1")
        legacy_mock_mode = _read_bool("MOCK_MODE", default=True)
        default_market_provider = "mock" if legacy_mock_mode else "massive"
        self.market_provider = os.getenv(
            "MARKET_PROVIDER", default_market_provider
        ).strip().lower()
        if self.market_provider not in {"mock", "massive", "kis", "hybrid"}:
            raise ValueError(
                "MARKET_PROVIDER must be 'mock', 'massive', 'kis', or 'hybrid'."
            )
        self.mock_mode = self.market_provider == "mock"
        self.kis_app_key = os.getenv("KIS_APP_KEY", "")
        self.kis_app_secret = os.getenv("KIS_APP_SECRET", "")
        self.dart_api_key = os.getenv("DART_API_KEY", "")
        self.massive_api_key = os.getenv("MASSIVE_API_KEY", "")
        symbols = os.getenv("MASSIVE_SYMBOLS", "NVDA")
        self.massive_symbols = tuple(
            dict.fromkeys(
                symbol.strip().upper() for symbol in symbols.split(",") if symbol.strip()
            )
        )
        self.massive_cache_seconds = int(os.getenv("MASSIVE_CACHE_SECONDS", "900"))
        if self.massive_cache_seconds <= 0:
            raise ValueError("MASSIVE_CACHE_SECONDS must be greater than zero.")
        kis_symbols = os.getenv("KIS_SYMBOLS", "005930")
        self.kis_symbols = tuple(
            dict.fromkeys(
                symbol.strip() for symbol in kis_symbols.split(",") if symbol.strip()
            )
        )
        self.kis_environment = os.getenv("KIS_ENVIRONMENT", "real").strip().lower()
        if self.kis_environment not in {"real", "demo"}:
            raise ValueError("KIS_ENVIRONMENT must be 'real' or 'demo'.")
        self.kis_cache_seconds = int(os.getenv("KIS_CACHE_SECONDS", "900"))
        if self.kis_cache_seconds <= 0:
            raise ValueError("KIS_CACHE_SECONDS must be greater than zero.")

    def api_status(self) -> dict[str, bool]:
        return {
            "kis_app_key": bool(self.kis_app_key),
            "kis_app_secret": bool(self.kis_app_secret),
            "dart_api_key": bool(self.dart_api_key),
            "massive_api_key": bool(self.massive_api_key),
        }


settings = Settings()
