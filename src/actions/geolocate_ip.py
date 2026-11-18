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

"""Look up one or more IP addresses in the MaxMind City database."""

import geoip2.errors
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, OutputField
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Param, Params

from ..database import lookup, validate_ip


class SparseGeoOutput(ActionOutput):
    def model_dump(self, **kwargs):
        # The legacy connector omits unavailable GeoIP fields from data and summaries.
        kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)


class GeoOutput(SparseGeoOutput):
    city_name: str | None = OutputField(example_values=["Ahmedabad"])
    state_name: str | None = OutputField(example_values=["Gujarat"])
    state_iso_code: str | None = OutputField(example_values=["GJ"])
    country_name: str | None = OutputField(example_values=["India"])
    country_iso_code: str | None = OutputField(example_values=["IN"])
    continent_name: str | None = OutputField(example_values=["Asia"])
    latitude: float | None = OutputField(example_values=[23.0333])
    longitude: float | None = OutputField(example_values=[72.6167])
    time_zone: str | None = OutputField(example_values=["Asia/Kolkata"])
    postal_code: str | None = OutputField(example_values=["380007"])
    as_number: int | None = None
    as_org: str | None = OutputField()
    domain: str | None = None


class GeoSummary(SparseGeoOutput):
    city: str | None = None
    state: str | None = None
    country: str | None = None


class GeolocateIpParams(Params):
    ip: str = Param(description="IP (IPv4/IPv6) to geolocate", primary=True, cef_types=["ip", "ipv6"], allow_list=True)


def _details(response) -> tuple[dict, dict]:
    data = {}
    summary = {}
    for section, attributes in (
        ("city", {"name": "city_name"}),
        ("country", {"name": "country_name", "iso_code": "country_iso_code"}),
        ("continent", {"name": "continent_name"}),
        ("location", {"latitude": "latitude", "longitude": "longitude", "time_zone": "time_zone"}),
        ("postal", {"code": "postal_code"}),
        ("traits", {"autonomous_system_number": "as_number", "autonomous_system_organization": "as_org", "domain": "domain"}),
    ):
        section_value = getattr(response, section, None)
        for source, target in attributes.items():
            value = getattr(section_value, source, None)
            if value is not None:
                data[target] = value
    subdivisions = getattr(response, "subdivisions", None)
    if subdivisions and len(subdivisions):
        subdivision = subdivisions.most_specific
        if subdivision.name is not None:
            data["state_name"] = subdivision.name
        if subdivision.iso_code is not None:
            data["state_iso_code"] = subdivision.iso_code
    for key, field in (("city_name", "city"), ("state_iso_code", "state"), ("country_name", "country")):
        if key in data:
            summary[field] = data[key]
    return data, summary


def geolocate_ip(params: GeolocateIpParams, soar: SOARClient) -> list[GeoOutput]:
    # The SDK converts each returned output model into a separate action result.
    ips = [part.strip() for part in params.ip.split(",")]
    if any(not validate_ip(ip) for ip in ips):
        raise ActionFailure("Please provide a valid IP Address")
    results = []
    for ip in ips:
        summary = {}
        try:
            response = lookup(ip)
        except geoip2.errors.AddressNotFoundError:
            # The legacy lookup returns a successful empty row for an address outside the database.
            output = GeoOutput()
            if len(ips) == 1:
                soar.set_message("IP not found")
        else:
            data, summary = _details(response)
            output = GeoOutput(**data)
            if len(ips) == 1:
                soar.set_summary(GeoSummary(**summary))
        results.append(output)
    return results
