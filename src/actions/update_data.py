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

"""Download and replace the MaxMind City database."""

from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionResult, OutputField, PermissiveActionOutput
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Params

from ..asset import Asset
from ..database import download_and_replace, redact


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


def update_data(params: Params, asset: Asset, soar: SOARClient):
    key = asset.license_key or ""
    try:
        if not key.strip():
            raise ActionFailure("License key is required to fetch MaxMind database.")
        headers = download_and_replace(key)
    except Exception as exc:
        result = ActionResult(False, f"Error in downloading or replacing database. {redact(exc, key)}")
        result.add_data({})
        return result
    soar.set_message("Successfully updated database.")
    return UpdateOutput(**headers)
