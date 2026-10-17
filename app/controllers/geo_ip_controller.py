from fastapi import APIRouter, Body, HTTPException
from app.dto_schemas.geoip_schemas import BulkGeoIPErrorResponse, GeoIPResponse
from app.services.geoip_service import GeoIPService
from app.utils.traceroute_parser import extract_ips_from_traceroute
from typing import Union

def create_geoip_controller(geoip_service: GeoIPService) -> APIRouter:
    router = APIRouter(prefix="/geoip", tags=["GeoIP"])

    @router.post("/bulk",response_model=list[Union[GeoIPResponse, BulkGeoIPErrorResponse]])
    def lookup_bulk(ips: list[str] = Body(..., min_length=1, max_length=500)):
        return geoip_service.lookup_bulk(ips)

    @router.get("/{ip}")
    def lookup_ip(ip: str):
        try:
            return geoip_service.get_geoip(ip)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except LookupError as e:
            raise HTTPException(404, str(e))

    @router.get("/asn/{ip}")
    def lookup_asn(ip: str):
        try:
            return geoip_service.get_asn(ip)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except LookupError as e:
            raise HTTPException(404, str(e))

    @router.get("/country/{ip}")
    def lookup_country(ip: str):
        try:
            return geoip_service.get_country(ip)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except LookupError as e:
            raise HTTPException(404, str(e))

    @router.post("/traceroute")
    def lookup_traceroute(traceroute_result: str = Body(..., media_type="text/plain")):
        try:
            ips = extract_ips_from_traceroute(traceroute_result)
            results = []

            for ip in ips:
                results.append(geoip_service.get_geoip(ip))

            return results
        except ValueError as e:
            raise HTTPException(400, str(e))
        except LookupError as e:
            raise HTTPException(404, str(e))
        except LookupError as e:
            raise HTTPException(404, str(e))

    return router
