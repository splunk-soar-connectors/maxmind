from pydantic import model_serializer
from soar_sdk.action_results import ActionOutput, OutputField, PermissiveActionOutput


class SparseGeoOutput(ActionOutput):
    @model_serializer(mode="wrap")
    def serialize_present_fields(self, handler):
        # The legacy connector omits unavailable GeoIP fields from data and summaries.
        return {key: value for key, value in handler(self).items() if value is not None}


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


class UpdateOutput(PermissiveActionOutput):
    # The server may add or remove HTTP headers; the documented common headers remain typed.
    date: str | None = OutputField(alias="Date")
    etag: str | None = OutputField(alias="ETag")
    expires: str | None = OutputField(alias="Expires")
    last_modified: str | None = OutputField(alias="Last-Modified")
    content_type: str | None = OutputField(alias="Content-Type")
    content_length: str | None = OutputField(alias="Content-Length")
    vary: str | None = OutputField(alias="Vary")
    cf_ray: str | None = OutputField(alias="CF-Ray")
    server: str | None = OutputField(alias="Server")
    expect_ct: str | None = OutputField(alias="expect-ct")
    connection: str | None = OutputField(alias="Connection")
    accept_ranges: str | None = OutputField(alias="Accept-Ranges")
    cache_control: str | None = OutputField(alias="Cache-Control")
    cf_cache_status: str | None = OutputField(alias="CF-Cache-Status")
    x_maxmind_worker: str | None = OutputField(alias="X-MaxMind-Worker")
    content_disposition: str | None = OutputField(alias="Content-Disposition")
