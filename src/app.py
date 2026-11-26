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

"""Splunk SOAR SDK app for MaxMind GeoIP2."""

from soar_sdk.app import App

from .actions import register_actions
from .asset import Asset
from .test_connectivity import run_test_connectivity


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
        run_test_connectivity(asset)

    return register_actions(app)


app = create_app()


if __name__ == "__main__":
    app.cli()
