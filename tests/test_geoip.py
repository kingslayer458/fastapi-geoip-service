import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.controllers.geo_ip_controller import create_geoip_controller
from app.dto_schemas.geoip_schemas import BulkGeoIPErrorResponse, GeoIPResponse
from app.services.geoip_service import GeoIPService


def geoip_record(ip: str) -> SimpleNamespace:
    return SimpleNamespace(
        country=SimpleNamespace(name="Example", iso_code="EX"),
        continent=SimpleNamespace(name="Exampleland"),
        subdivisions=SimpleNamespace(most_specific=SimpleNamespace(name="Example")),
        city=SimpleNamespace(name="Example City"),
        postal=SimpleNamespace(code="12345"),
        location=SimpleNamespace(
            latitude=1.0, longitude=2.0, time_zone="UTC"
        ),
        network=f"{ip}/32",
    )


class GeoIPServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = Mock()
        self.service = GeoIPService(self.repository)

    def test_public_lookup_and_asn_only_lookup(self) -> None:
        self.repository.get_city.return_value = None
        self.repository.get_country.return_value = None
        self.repository.get_asn.return_value = SimpleNamespace(
            autonomous_system_number=13335,
            autonomous_system_organization="Cloudflare",
            network="1.1.1.0/24",
        )

        result = self.service.get_geoip("1.1.1.1")

        self.assertIsInstance(result, GeoIPResponse)
        self.assertEqual(result.asn, 13335)
        self.assertIsNone(result.country)

    def test_city_country_and_ipv6_lookup(self) -> None:
        self.repository.get_city.return_value = geoip_record("8.8.8.8")
        self.repository.get_country.return_value = geoip_record("8.8.8.8")
        self.repository.get_asn.return_value = None

        result = self.service.get_geoip("2001:4860:4860::8888")

        self.assertEqual(result.country, "Example")
        self.assertEqual(result.city, "Example City")

    def test_country_only_lookup_is_successful(self) -> None:
        self.repository.get_city.return_value = None
        self.repository.get_country.return_value = geoip_record("8.8.8.8")
        self.repository.get_asn.return_value = None

        result = self.service.get_geoip("8.8.8.8")

        self.assertEqual(result.country, "Example")
        self.assertEqual(result.continent, "Exampleland")
        self.assertIsNone(result.city)

    def test_bulk_returns_item_errors_and_keeps_successes(self) -> None:
        self.repository.get_city.side_effect = [
            geoip_record("8.8.8.8"),
            None,
        ]
        self.repository.get_country.side_effect = [
            geoip_record("8.8.8.8"),
            None,
        ]
        self.repository.get_asn.side_effect = [
            None,
            None,
        ]

        results = self.service.lookup_bulk(
            ["8.8.8.8", "228.104.147.134", "999.999.999.999", "45.45.45.45"]
        )

        self.assertIsInstance(results[0], GeoIPResponse)
        self.assertEqual(results[1].status, "unsupported")
        self.assertEqual(results[2].status, "invalid")
        self.assertEqual(results[3].status, "not_found")

    def test_private_and_loopback_are_unsupported(self) -> None:
        results = self.service.lookup_bulk(["192.168.1.1", "127.0.0.1"])

        self.assertEqual([result.status for result in results], ["unsupported", "unsupported"])
        self.repository.get_city.assert_not_called()

    def test_empty_and_duplicate_inputs(self) -> None:
        self.repository.get_city.return_value = geoip_record("8.8.8.8")
        self.repository.get_country.return_value = None
        self.repository.get_asn.return_value = None

        results = self.service.lookup_bulk([])
        self.assertEqual(results, [])

        results = self.service.lookup_bulk(["8.8.8.8", "8.8.8.8"])
        self.assertEqual(len(results), 2)
        self.assertEqual(self.repository.get_city.call_count, 2)

    def test_unexpected_repository_error_is_safe(self) -> None:
        self.repository.get_city.side_effect = RuntimeError("database unavailable")

        result = self.service.lookup_bulk(["8.8.8.8"])[0]

        self.assertIsInstance(result, BulkGeoIPErrorResponse)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.error, "GeoIP lookup failed")

    def test_routes_make_bulk_post_only(self) -> None:
        routes = create_geoip_controller(self.service).routes
        bulk_routes = [route for route in routes if route.path == "/geoip/bulk"]

        self.assertEqual([route.methods for route in bulk_routes], [{"POST"}])
        self.assertIsNotNone(bulk_routes[0].response_model)
        body_field = bulk_routes[0].dependant.body_params[0]
        self.assertEqual(body_field.field_info.metadata[0].min_length, 1)
        self.assertEqual(body_field.field_info.metadata[1].max_length, 500)

    def test_traceroute_keeps_private_hops_as_bulk_errors(self) -> None:
        self.repository.get_city.return_value = geoip_record("8.8.8.8")
        self.repository.get_country.return_value = geoip_record("8.8.8.8")
        self.repository.get_asn.return_value = None
        controller = create_geoip_controller(self.service)
        traceroute_route = next(
            route for route in controller.routes if route.path == "/geoip/traceroute"
        )

        result = traceroute_route.endpoint(
            "traceroute to example (192.168.1.1)\n 1 192.168.1.1\n 2 8.8.8.8"
        )

        self.assertEqual(result[0].ip, "192.168.1.1")
        self.assertEqual(result[0].status, "unsupported")
        self.assertIn("reserved IP address", result[0].error)
        self.assertEqual(result[1].ip, "8.8.8.8")


if __name__ == "__main__":
    unittest.main()
