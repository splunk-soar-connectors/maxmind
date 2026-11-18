# Copyright (c) 2026 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test local database and optional MaxMind web-service connectivity."""

import ipaddress

import geoip2.errors
import requests
from soar_sdk.exceptions import ActionFailure
from soar_sdk.logging import getLogger

from .asset import Asset
from .client import web_service_base_url
from .database import DB_PATH, lookup


logger = getLogger()
DEFAULT_TIMEOUT = 30


def run_test_connectivity(asset: Asset) -> None:
    """Validate the local database and configured MaxMind web service."""
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
