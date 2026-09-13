from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.paths.root import API_V1
from app.controllers.geo_ip_controller import create_geoip_controller
from app.controllers.health_controller import router as health_router
from app.config import settings
from app.repositories.geoip_repo import GeoIPRepository
from app.services.geoip_service import GeoIPService


repository = GeoIPRepository(
    geoip_path=settings.geoip_path,
    country_db=settings.country_db,
    city_db=settings.city_db,
    asn_db=settings.asn_db,
)


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("Initializing GeoIP databases...")

    repository.initialize()

    missing_databases = repository.missing_databases()

    if missing_databases:
        print(
            "Warning: missing GeoLite database files: "
            + ", ".join(missing_databases)
        )
    else:
        print("All GeoLite database files are present")

    print("GeoIP databases initialized")

    yield

    print("Closing GeoIP databases...")

    repository.close()


app = FastAPI(
    title="kingslayer GeoIP API",
    version="1.0.0",
    lifespan=lifespan,
)


geoip_service = GeoIPService(repository)

geoip_router = create_geoip_controller(geoip_service)

app.include_router(health_router)
app.include_router(geoip_router, prefix=API_V1)