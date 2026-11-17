"""Splunk SOAR SDK app for MaxMind GeoIP2."""

import ipaddress

import geoip2.errors
import requests
from soar_sdk.app import App
from soar_sdk.exceptions import ActionFailure
from soar_sdk.logging import getLogger

from .actions import register_actions
from .asset import Asset
from .database import DB_PATH, lookup
from .web_service import web_service_base_url


logger = getLogger()
DEFAULT_TIMEOUT = 30


def create_app() -> App:
    app = App(
        name="MaxMind",
        app_type="information",
        logo="logo_maxmind.svg",
        logo_dark="logo_maxmind_dark.svg",
        product_vendor="MaxMind",
        product_name="GeoIP2",
        publisher="Splunk",
        appid="c566e153-3118-4033-abda-14dd9748c91a",
        fips_compliant=True,
        python_version="3.13",
        min_phantom_version="7.0.0",
        asset_cls=Asset,
    )

    @app.test_connectivity()
    def test_connectivity(asset: Asset) -> None:
        ip = asset.ip_address or "8.8.8.8"
        try:
            ipaddress.ip_address(ip)
        except ValueError as exc:
            raise ActionFailure("Please provide a valid IP Address in the configuration parameters") from exc
        try:
            lookup(ip)
        except geoip2.errors.AddressNotFoundError:
            logger.progress(f"Successfully able to query the MaxMind DB for the IP: '{ip}'. But, the requested IP not found.")
        except Exception as exc:
            raise ActionFailure(f"MaxMind DB load failed for: '{DB_PATH}': {exc}") from exc
        else:
            logger.progress(f"Successfully able to query the MaxMind DB for the IP: '{ip}'")

        if asset.account_id and asset.license_key:
            service, base_url = web_service_base_url(asset.web_service)
            try:
                response = requests.get(
                    f"{base_url}/geoip/v2.1/country/me",
                    auth=(asset.account_id, asset.license_key),
                    headers={"Accept": "application/json"},
                    timeout=DEFAULT_TIMEOUT,
                )
            except requests.RequestException as exc:
                raise ActionFailure(f"Unable to connect to the MaxMind {service} web service: {exc}") from exc
            if not response.ok:
                raise ActionFailure(f"MaxMind {service} web-service authentication failed with status code: {response.status_code}")

        logger.progress("Test Connectivity Passed")

    return register_actions(app)


app = create_app()


if __name__ == "__main__":
    app.cli()
