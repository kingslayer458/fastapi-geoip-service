import ipaddress
from app.repositories.geoip_repo import GeoIPRepository
from app.dto_schemas.geoip_schemas import (
    ASNResponse,
    CountryResponse,
    GeoIPResponse,
)


class GeoIPService:

    def __init__(self, repository: GeoIPRepository):
        self.repository = repository

    def validate_ip(self, ip: str):

        try:
            return ipaddress.ip_address(ip)

        except ValueError:
            raise ValueError(f"Invalid IP address: {ip}")

    def reserved_ip_response(self, ip: str):
        return {
            "message": f"The IP address '{ip}' is a reserved IP address",
        }

    def get_asn(self, ip: str):

        ip_obj = self.validate_ip(ip)

        if not ip_obj.is_global:
            return self.reserved_ip_response(ip)

        response = self.repository.get_asn(ip)

        if response is None:
            raise LookupError(f"IP address not found: {ip}")

        network = None

        if response.network:
            network = str(response.network)

        return ASNResponse(
            ip=ip,
            asn=response.autonomous_system_number,
            organization=response.autonomous_system_organization,
            network=network,
        )

    def get_country(self, ip: str):

        ip_obj = self.validate_ip(ip)

        if not ip_obj.is_global:
            return self.reserved_ip_response(ip)

        country = self.repository.get_country(ip)

        if country is None:
            raise LookupError(f"IP address not found: {ip}")

        return CountryResponse(
            ip=ip,
            country=country.country.name,
            country_iso=country.country.iso_code,
            continent=country.continent.name,
        )

    def get_geoip(self, ip: str):

        ip_obj = self.validate_ip(ip)

        if not ip_obj.is_global:
            return self.reserved_ip_response(ip)

        city = self.repository.get_city(ip)
        country = self.repository.get_country(ip)
        asn = self.repository.get_asn(ip)

        if city is None and country is None and asn is None:
            raise LookupError(f"IP address not found: {ip}")

        return GeoIPResponse(
            ip=ip,
            country=city.country.name if city else country.country.name if country else None,
            country_iso=city.country.iso_code if city else country.country.iso_code if country else None,
            continent=city.continent.name if city else None,
            region=(city.subdivisions.most_specific.name if city else None ),
            city=city.city.name if city else None,
            postal_code=(city.postal.code if city else None),
            latitude=(city.location.latitude if city else None),
            longitude=(city.location.longitude if city else None),
            timezone=(city.location.time_zone if city else None),
            asn=(asn.autonomous_system_number if asn else None ),
            organization=(asn.autonomous_system_organization if asn else None),
            network=str(asn.network) if asn and asn.network else None,
        )
