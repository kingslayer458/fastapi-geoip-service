from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings
import logging
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    geoip_path: Path = BASE_DIR / "geoip_database"

    country_db: str = "GeoLite2-Country.mmdb"
    city_db: str = "GeoLite2-City.mmdb"
    asn_db: str = "GeoLite2-ASN.mmdb"
    cors_origins: str = ""

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: str) -> str:
        if not value.strip():
            logger.warning("WARNING: CORS_ORIGINS is Empty")
        return value


settings = Settings()