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

"""Register MaxMind actions."""

from collections.abc import Iterator

from soar_sdk.app import App
from soar_sdk.models.container import Container
from soar_sdk.params import OnPollParams

from ..asset import Asset
from ..render_meta import preserve_render_metadata
from .geolocate_ip import GeolocateIpParams, GeoOutput, GeoSummary, geolocate_ip
from .make_request import make_request
from .on_poll import run_on_poll
from .update_data import UpdateOutput, update_data


def register_actions(app: App) -> App:
    app.make_request()(make_request)
    app.action(
        name="geolocate ip",
        identifier="lookup_ip",
        description="Queries MaxMind for IP location info",
        action_type="investigate",
        read_only=True,
        params_class=GeolocateIpParams,
        output_class=GeoOutput,
        summary_type=GeoSummary,
        flatten_results=False,
    )(geolocate_ip)
    app.register_action(
        action=update_data,
        name="update data",
        identifier="update_database",
        description="Update database used to locate an ip",
        verbose="This app uses the MaxMind GeoLite2 City database.",
        action_type="generic",
        read_only=False,
        output_class=UpdateOutput,
    )

    @app.on_poll()
    def on_poll(params: OnPollParams, asset: Asset) -> Iterator[Container]:
        """Update the database if there is a newer one and yield an empty container."""
        yield from run_on_poll(params, asset)

    preserve_render_metadata(app)
    return app
