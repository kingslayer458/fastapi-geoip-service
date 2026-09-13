from app.config import settings
from app.services.geoip_service import GeoIPService
from app.repositories.geoip_repo import GeoIPRepository

repository = GeoIPRepository(
    geoip_path=settings.geoip_path,
    country_db=settings.country_db,
    city_db=settings.city_db,
    asn_db=settings.asn_db,
)

repository.initialize()

xy = GeoIPService(repository)

xys = "192.168.1.1"
findd = xy.get_geoip(xys)

print(findd)

repository.close()
