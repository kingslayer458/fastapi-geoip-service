from pathlib import Path
from typing import Optional

import geoip2.database
from geoip2.errors import AddressNotFoundError


class GeoIPRepository:

    def __init__(self, geoip_path: str, country_db: str, city_db: str, asn_db: str):
        self.geoip_path = Path(geoip_path)

        self.country_db_path = self.geoip_path / country_db
        self.city_db_path = self.geoip_path / city_db
        self.asn_db_path = self.geoip_path / asn_db

        self.country_reader: Optional[geoip2.database.Reader] = None
        self.city_reader: Optional[geoip2.database.Reader] = None
        self.asn_reader: Optional[geoip2.database.Reader] = None

    def initialize(self):
        """
        Open MaxMind databases.
        """

        if self.country_db_path.exists():
            self.country_reader = geoip2.database.Reader(str(self.country_db_path))

        if self.city_db_path.exists():
            self.city_reader = geoip2.database.Reader(str(self.city_db_path))

        if self.asn_db_path.exists():
            self.asn_reader = geoip2.database.Reader(str(self.asn_db_path))

    def missing_databases(self) -> list[str]:
        missing = []

        if not self.country_db_path.exists():
            missing.append(self.country_db_path.name)

        if not self.city_db_path.exists():
            missing.append(self.city_db_path.name)

        if not self.asn_db_path.exists():
            missing.append(self.asn_db_path.name)

        return missing

    def get_country(self, ip: str):
        if not self.country_reader:
            return None

        try:
            return self.country_reader.country(ip)

        except AddressNotFoundError:
            return None

    def get_city(self, ip: str):
        if not self.city_reader:
            return None

        try:
            return self.city_reader.city(ip)

        except AddressNotFoundError:
            return None

    def get_asn(self, ip: str):
        if not self.asn_reader:
            raise RuntimeError("ASN database is not available")

        try:
            return self.asn_reader.asn(ip)

        except AddressNotFoundError:
            return None

    def close(self):
        if self.country_reader:
            self.country_reader.close()

        if self.city_reader:
            self.city_reader.close()

        if self.asn_reader:
            self.asn_reader.close()