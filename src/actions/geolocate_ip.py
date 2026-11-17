"""Look up one or more IP addresses in the MaxMind City database."""

import geoip2.errors
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionResult
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Param, Params

from ..database import lookup, validate_ip
from ..models import GeoOutput, GeoSummary


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


def geolocate_ip(params: GeolocateIpParams, soar: SOARClient):
    # The legacy allow_list action returns a separate action result for every address.
    ips = [part.strip() for part in params.ip.split(",")]
    if any(not validate_ip(ip) for ip in ips):
        raise ActionFailure("Please provide a valid IP Address")
    results = []
    for ip in ips:
        try:
            response = lookup(ip)
        except geoip2.errors.AddressNotFoundError:
            # The legacy lookup returns a successful empty row for an address outside the database.
            result = ActionResult(True, "", {"ip": ip})
            result.set_status(True, "IP not found")
            result.add_data({})
        else:
            data, summary = _details(response)
            output = GeoOutput(**data)
            if len(ips) == 1:
                soar.set_summary(GeoSummary(**summary))
                return output
            # Multiple IPs need separate parameters and summaries in the action results.
            result = ActionResult(True, "", {"ip": ip})
            result.add_data(output.model_dump(exclude_none=True))
            result.set_summary(summary)
        results.append(result)
    return results
