"""Application configuration via environment variables with sensible defaults.

Pattern adopted from itskovacs/trip: Pydantic Settings with env-driven config
and zero-config defaults so the app runs out of the box.
"""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "NYC Pedestrian Analysis"
    DEBUG: bool = False

    # Database
    DB_PATH: str = "storage/nyc_ped.db"

    # Data source API keys (optional -- public endpoints work without keys)
    NYC_OPENDATA_APP_TOKEN: str = ""

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Frontend
    STATIC_DIR: str = "static"

    @property
    def database_url(self) -> str:
        Path(self.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{self.DB_PATH}"

    model_config = {"env_prefix": "NYP_"}


settings = Settings()
