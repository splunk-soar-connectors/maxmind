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

"""Call the authenticated MaxMind GeoIP or GeoLite web service."""

import ipaddress
import json

import requests
from soar_sdk.action_results import MakeRequestOutput
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import MakeRequestParams, Param

from ..asset import Asset
from ..client import SERVICES, web_service_base_url


DEFAULT_TIMEOUT = 30


class MaxMindMakeRequestParams(MakeRequestParams):
    endpoint: str = Param(
        description="GeoIP web-service path, for example /geoip/v2.1/city/8.8.8.8",
        required=True,
    )


def _endpoint(value: str, web_service: str) -> str:
    endpoint = value.strip()
    if endpoint.startswith(("http://", "https://")):
        raise ActionFailure("Provide a GeoIP web-service path, not a full URL")
    if "?" in endpoint or "#" in endpoint:
        raise ActionFailure("Use query parameters instead of including them in the endpoint")

    parts = endpoint.strip("/").split("/")
    if len(parts) != 4 or parts[:2] != ["geoip", "v2.1"]:
        raise ActionFailure("Endpoint must be /geoip/v2.1/{country|city|insights}/{ip_address}")

    service, ip_address = parts[2:]
    if service not in SERVICES[web_service]:
        allowed = ", ".join(sorted(SERVICES[web_service]))
        raise ActionFailure(f"{web_service} supports these services: {allowed}")
    if ip_address != "me":
        try:
            ipaddress.ip_address(ip_address)
        except ValueError as exc:
            raise ActionFailure("Endpoint must contain a valid IP address or 'me'") from exc
    return f"/{'/'.join(parts)}"


def _headers(value: str | None) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if not value:
        return headers
    try:
        supplied = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ActionFailure("Invalid JSON headers") from exc
    if not isinstance(supplied, dict) or not all(isinstance(key, str) and isinstance(item, str) for key, item in supplied.items()):
        raise ActionFailure("Headers must be a JSON object with string keys and values")
    if any(key.lower() in {"authorization", "host", "proxy-authorization"} for key in supplied):
        raise ActionFailure("Authorization, Host, and Proxy-Authorization headers cannot be overridden")
    headers.update(supplied)
    return headers


def _query_parameters(value: str | None) -> dict | str | None:
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return value.lstrip("?")
    if not isinstance(parsed, dict):
        raise ActionFailure("Query parameters must be a JSON object or query string")
    return parsed


def make_request(params: MaxMindMakeRequestParams, asset: Asset) -> MakeRequestOutput:
    """Make a live, authenticated GeoIP or GeoLite web-service request."""
    if not asset.account_id or not asset.license_key:
        raise ActionFailure("Account ID and license key are required for Make Request")
    if params.http_method != "GET":
        raise ActionFailure("MaxMind GeoIP web-service requests must use GET")
    if params.body:
        raise ActionFailure("MaxMind GeoIP web-service requests do not accept a request body")
    if params.timeout is not None and params.timeout <= 0:
        raise ActionFailure("Timeout must be greater than zero")

    web_service, base_url = web_service_base_url(asset.web_service)
    endpoint = _endpoint(params.endpoint, web_service)

    try:
        response = requests.get(
            base_url + endpoint,
            auth=(asset.account_id, asset.license_key),
            headers=_headers(params.headers),
            params=_query_parameters(params.query_parameters),
            timeout=params.timeout or DEFAULT_TIMEOUT,
            verify=params.verify_ssl,
        )
    except requests.RequestException as exc:
        raise ActionFailure(f"Request failed: {exc}") from exc
    return MakeRequestOutput(status_code=response.status_code, response_body=response.text)
