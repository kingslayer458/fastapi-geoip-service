from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings

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
            raise ValueError("CORS_ORIGINS must be configured")
        return value


settings = Settings()