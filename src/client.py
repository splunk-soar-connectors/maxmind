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
