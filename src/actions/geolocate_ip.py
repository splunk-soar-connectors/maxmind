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
from soar_sdk.action_results import ActionOutput, ActionResult, OutputField
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Param, Params

from ..database import lookup, validate_ip


class SparseGeoOutput(ActionOutput):
    def __init__(self, **data):
        super().__init__(**data)
        # ActionOutput fills omitted optional fields with None during validation.
        self.model_fields_set.intersection_update(data)

    def model_dump(self, **kwargs):
        # Unavailable fields are omitted unless legacy explicitly emitted them as null.
        kwargs["exclude_unset"] = True
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
    if "country_name" not in data:
        data.pop("country_iso_code", None)
    subdivisions = getattr(response, "subdivisions", None)
    if subdivisions and len(subdivisions):
        subdivision = subdivisions.most_specific
        data["state_name"] = subdivision.name
        data["state_iso_code"] = subdivision.iso_code
    for key, field in (("city_name", "city"), ("state_iso_code", "state"), ("country_name", "country")):
        if key in data:
            summary[field] = data[key]
    return data, summary


def _lookup_ip(ip: str) -> tuple[GeoOutput, GeoSummary, str]:
    try:
        response = lookup(ip)
    except geoip2.errors.AddressNotFoundError:
        return GeoOutput(), GeoSummary(), "IP not found"
    data, summary = _details(response)
    return GeoOutput(**data), GeoSummary(**summary), ""


def geolocate_ip(params: GeolocateIpParams, soar: SOARClient):
    """Return typed location data, with independent legacy result metadata for IP lists."""
    input_ips = [part.strip() for part in params.ip.split(",")]
    is_ip_list = len(input_ips) > 1
    ips = list(dict.fromkeys(input_ips))
    if any(not validate_ip(ip) for ip in ips):
        raise ActionFailure("Please provide a valid IP Address")
    if len(ips) == 1 and not is_ip_list:
        output, summary, message = _lookup_ip(ips[0])
        soar.set_summary(summary)
        soar.set_message(message)
        return output

    # With typed outputs alone the SDK uses one shared parameter, summary and message for every row.
    # Use ActionResult only for batches so each IP has its own metadata and failures keep other rows.
    results = []
    for ip in ips:
        param = {"ip": ip}
        try:
            output, summary, message = _lookup_ip(ip)
        except Exception as exc:
            result = ActionResult(status=False, message=f"Failed to geolocate IP {ip}: {exc}", param=param)
        else:
            result = ActionResult(status=True, message=message, param=param)
            result.add_data(output.model_dump(by_alias=True))
            result.set_summary(summary.model_dump(by_alias=True))
        results.append(result)
    return results
