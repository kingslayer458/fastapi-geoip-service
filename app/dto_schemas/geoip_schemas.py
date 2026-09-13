from typing import Optional
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    message: str


class CityResponse(BaseModel):
    ip: str
    country: Optional[str] = None
    country_iso: Optional[str] = None
    continent: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None


class CountryResponse(BaseModel):
    ip: str
    country: Optional[str] = None
    country_iso: Optional[str] = None
    continent: Optional[str] = None
    error: Optional[ErrorResponse] = None


class ASNResponse(BaseModel):
    ip: str
    asn: Optional[int] = None
    organization: Optional[str] = None
    network: Optional[str] = None
    error: Optional[ErrorResponse] = None


class GeoIPResponse(BaseModel):
    ip: str
    country: Optional[str] = None
    country_iso: Optional[str] = None
    continent: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    asn: Optional[int] = None
    organization: Optional[str] = None
    network: Optional[str] = None
    error: Optional[ErrorResponse] = None
