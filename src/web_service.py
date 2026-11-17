"""Shared configuration for MaxMind GeoIP and GeoLite web services."""

from soar_sdk.exceptions import ActionFailure


BASE_URLS = {
    "GeoLite": "https://geolite.info",
    "GeoIP": "https://geoip.maxmind.com",
}
SERVICES = {
    "GeoLite": {"city", "country"},
    "GeoIP": {"city", "country", "insights"},
}


def web_service_base_url(web_service: str | None) -> tuple[str, str]:
    """Return the configured MaxMind web-service name and base URL."""
    service = web_service or "GeoLite"
    if service not in BASE_URLS:
        raise ActionFailure("Web service must be GeoLite or GeoIP")
    return service, BASE_URLS[service]
