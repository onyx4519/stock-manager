import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


class Settings:
    def __init__(self):
        self.kis_app_key = os.getenv("KIS_APP_KEY", "")
        self.kis_app_secret = os.getenv("KIS_APP_SECRET", "")
        self.dart_api_key = os.getenv("DART_API_KEY", "")
        self.massive_api_key = os.getenv("MASSIVE_API_KEY", "")

    def api_status(self) -> dict[str, bool]:
        return {
            "kis_app_key": bool(self.kis_app_key),
            "kis_app_secret": bool(self.kis_app_secret),
            "dart_api_key": bool(self.dart_api_key),
            "massive_api_key": bool(self.massive_api_key),
        }


settings = Settings()