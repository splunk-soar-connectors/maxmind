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

"""Behavior and contract checks for the converted MaxMind app."""

import io
import json
import tarfile
from unittest.mock import Mock, patch

import pytest
from soar_sdk.exceptions import ActionFailure
from soar_sdk.models.container import Container
from soar_sdk.params import OnPollParams, Params
from soar_sdk.shims.phantom.encryption_helper import encryption_helper

from src.actions.geolocate_ip import GeolocateIpParams, GeoOutput, geolocate_ip
from src.actions.make_request import MaxMindMakeRequestParams, make_request
from src.actions.on_poll import run_on_poll
from src.actions.update_data import UpdateOutput, update_data
from src.app import app
from src.asset import Asset
from src.database import download_and_replace


def run_action(identifier, params=None, config=None):
    if hasattr(app, "_asset"):
        del app._asset
    app.actions_manager.action_results = []
    if config and "license_key" in config:
        config = {**config, "license_key": encryption_helper.encrypt(config["license_key"], "123")}
    app.handle(
        json.dumps(
            {
                "identifier": identifier,
                "asset_id": "123",
                "config": {"app_version": "2.4.2", "directory": ".", "main_module": "src.app:app", **(config or {})},
                "parameters": [params or {}],
            }
        )
    )
    return app.actions_manager.get_results()


def test_geolocate_multiple_ips_returns_declared_output_rows():
    results = run_action("lookup_ip", {"ip": "8.8.8.8,1.1.1.1"})
    assert len(results) == 2
    assert all(result.get_status() for result in results)
    assert results[0].get_data()[0]["country_iso_code"] == "US"
    assert "latitude" in results[0].get_data()[0]
    assert results[0].get_summary() == {}
    assert results[1].get_summary() == {}


def test_single_ip_returns_declared_model_without_missing_fields():
    outputs = geolocate_ip(GeolocateIpParams(ip="8.8.8.8"), Mock())
    assert len(outputs) == 1
    assert isinstance(outputs[0], GeoOutput)
    assert outputs[0].model_dump()["country_iso_code"] == "US"
    assert None not in outputs[0].model_dump().values()

    result = run_action("lookup_ip", {"ip": "8.8.8.8"})[-1]
    assert result.get_data() == [outputs[0].model_dump()]
    assert result.get_summary() == {"country": "United States"}


@pytest.mark.parametrize("ip", ["8.8.8", "splunk.com", "https://www.splunk.com", "8.8.8.8 1.1.1.1"])
def test_invalid_ip_fails(ip):
    result = run_action("lookup_ip", {"ip": ip})[-1]
    assert not result.get_status()
    assert result.get_data() == []


def test_valid_ip_not_in_database_is_success_with_empty_data():
    result = run_action("lookup_ip", {"ip": "255.255.255.255"})[-1]
    assert result.get_status()
    assert result.get_message() == "IP not found"
    assert result.get_data() == [{}]


def test_geolocate_returns_results_for_multiple_ips():
    outputs = geolocate_ip(GeolocateIpParams(ip="8.8.8.8,1.1.1.1"), Mock())
    assert len(outputs) == 2
    assert all(isinstance(output, GeoOutput) for output in outputs)


def test_connectivity_accepts_missing_ip_and_rejects_bad_asset_ip():
    assert run_action("test_connectivity", config={"ip_address": "255.255.255.255"})[-1].get_status()
    assert not run_action("test_connectivity", config={"ip_address": "invalid"})[-1].get_status()


def test_connectivity_validates_configured_web_service_credentials():
    response = Mock(ok=True, status_code=200)
    with patch("src.test_connectivity.requests.get", return_value=response) as request:
        result = run_action("test_connectivity", config={"account_id": "123", "license_key": "secret"})[-1]
    assert result.get_status()
    assert request.call_args.args[0] == "https://geolite.info/geoip/v2.1/country/me"
    assert request.call_args.kwargs["auth"] == ("123", "secret")


def test_connectivity_fails_for_invalid_web_service_credentials():
    response = Mock(ok=False, status_code=401)
    with patch("src.test_connectivity.requests.get", return_value=response):
        result = run_action("test_connectivity", config={"account_id": "123", "license_key": "secret"})[-1]
    assert not result.get_status()
    assert "authentication failed with status code: 401" in result.get_message()


def test_make_request_calls_configured_web_service_with_basic_authentication():
    response = Mock(status_code=200, text='{"country": {"iso_code": "US"}}')
    asset = Asset(account_id="123", license_key="secret", web_service="GeoLite")
    params = MaxMindMakeRequestParams(
        http_method="GET",
        endpoint="/geoip/v2.1/city/8.8.8.8",
        headers='{"Accept-Language": "en"}',
        query_parameters='{"pretty": "true"}',
    )
    with patch("src.actions.make_request.requests.get", return_value=response) as request:
        output = make_request(params, asset)
    assert output.status_code == 200
    assert output.response_body == response.text
    assert request.call_args.args[0] == "https://geolite.info/geoip/v2.1/city/8.8.8.8"
    assert request.call_args.kwargs["auth"] == ("123", "secret")
    assert request.call_args.kwargs["headers"] == {"Accept": "application/json", "Accept-Language": "en"}
    assert request.call_args.kwargs["params"] == {"pretty": "true"}


def test_make_request_returns_api_errors_as_response_data():
    response = Mock(status_code=401, text='{"code": "AUTHORIZATION_INVALID"}')
    with patch("src.actions.make_request.requests.get", return_value=response):
        result = run_action(
            "make_request",
            {"http_method": "GET", "endpoint": "/geoip/v2.1/country/8.8.8.8"},
            {"account_id": "123", "license_key": "secret"},
        )[-1]
    assert result.get_status()
    assert result.get_data() == [{"status_code": 401, "response_body": response.text}]


@pytest.mark.parametrize(
    "params, asset",
    [
        (
            MaxMindMakeRequestParams(http_method="POST", endpoint="/geoip/v2.1/city/8.8.8.8"),
            Asset(account_id="123", license_key="secret"),
        ),
        (
            MaxMindMakeRequestParams(http_method="GET", endpoint="https://geolite.info/geoip/v2.1/city/8.8.8.8"),
            Asset(account_id="123", license_key="secret"),
        ),
        (
            MaxMindMakeRequestParams(http_method="GET", endpoint="/geoip/v2.1/insights/8.8.8.8"),
            Asset(account_id="123", license_key="secret"),
        ),
        (
            MaxMindMakeRequestParams(http_method="GET", endpoint="/geoip/v2.1/city/8.8.8.8", body="{}"),
            Asset(account_id="123", license_key="secret"),
        ),
        (
            MaxMindMakeRequestParams(http_method="GET", endpoint="/geoip/v2.1/city/8.8.8.8"),
            Asset(license_key="secret"),
        ),
        (
            MaxMindMakeRequestParams(
                http_method="GET",
                endpoint="/geoip/v2.1/city/8.8.8.8",
                headers='{"Authorization": "Basic caller-value"}',
            ),
            Asset(account_id="123", license_key="secret"),
        ),
    ],
)
def test_make_request_rejects_unsupported_or_incomplete_requests(params, asset):
    with pytest.raises(ActionFailure):
        make_request(params, asset)


def test_poll_requires_license_key():
    result = run_action("on_poll")[-1]
    assert not result.get_status()
    assert "License key is required" in result.get_message()


def test_poll_reuses_legacy_checkpoint_and_creates_empty_container():
    asset = Asset(license_key="secret")

    class State(dict):
        backend = type("Backend", (), {"load_state": lambda self: {"db_last_modified_time": "Mon, 01 Jan 2024 00:00:00 GMT"}})()

    state = State()
    asset._ingest_state = state
    with (
        patch("src.actions.on_poll.check_newer", return_value=False) as check,
        patch("src.actions.on_poll.download_and_replace") as update,
        patch.object(app.actions_manager, "save_container", return_value=(True, "saved", 42)) as save,
    ):
        containers = list(run_on_poll(OnPollParams(), asset))
    assert check.call_args.args[1]["db_last_modified_time"] == "Mon, 01 Jan 2024 00:00:00 GMT"
    update.assert_not_called()
    assert isinstance(containers[0], Container)
    assert containers[0].name.startswith("maxmind_ingestion_")
    assert containers[0].run_automation
    save.assert_not_called()


def test_update_failure_redacts_license_key():
    with patch("src.actions.update_data.download_and_replace", side_effect=RuntimeError("https://example/?license_key=bad%2Bkey")):
        result = run_action("update_database", config={"license_key": "bad+key"})[-1]
    assert not result.get_status()
    assert "bad+key" not in result.get_message()
    assert "bad%2Bkey" not in result.get_message()


def test_download_rejects_bad_archive_without_replacing_database(tmp_path):
    db = tmp_path / "GeoLite2-City.mmdb"
    db.write_bytes(b"old data")
    archive_bytes = io.BytesIO()
    with tarfile.open(fileobj=archive_bytes, mode="w:gz") as archive:
        payload = b"not a database"
        member = tarfile.TarInfo("../../GeoLite2-City.mmdb")
        member.size = len(payload)
        archive.addfile(member, io.BytesIO(payload))

    class Response:
        status_code = 200
        headers = {"last-modified": "Tue, 02 Jan 2024 00:00:00 GMT"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def iter_content(self, chunk_size):
            yield archive_bytes.getvalue()

    state = {}
    with patch("src.database.requests.get", return_value=Response()), pytest.raises(Exception):
        download_and_replace("secret", state, db)
    assert db.read_bytes() == b"old data"
    assert state == {}
    assert list(tmp_path.iterdir()) == [db]


def test_manifest_keeps_map_and_documented_output_paths():
    geolocate = app.actions_manager.get_action("lookup_ip").meta.model_dump()
    assert geolocate["render"] == {"type": "map", "width": 10, "height": 5, "title": "IP Geolocation"}
    update = app.actions_manager.get_action("update_database").meta.model_dump()
    assert update["render"] == {"type": "table", "width": 12, "height": 5, "title": "Update Database"}
    paths = {field["data_path"] for field in geolocate["output"]}
    assert {"action_result.data.*.latitude", "action_result.data.*.longitude", "action_result.summary.country"} <= paths
    assert next(field for field in geolocate["output"] if field["data_path"] == "action_result.parameter.ip")["map_info"] == "name"


def test_update_data_returns_response_headers():
    headers = {
        "Date": "Mon, 03 Jan 2022 19:37:02 GMT",
        "Last-Modified": "Tue, 28 Dec 2021 17:52:24 GMT",
        "Expires": "Mon, 03 Jan 2022 19:37:02 GMT",
    }
    with patch("src.actions.update_data.download_and_replace", return_value=headers) as update:
        result = run_action("update_database", config={"license_key": "secret"})[-1]
    assert result.get_status()
    assert result.get_message() == "Successfully updated database."
    assert result.get_data() == [headers]
    assert update.call_args.args[0] == "secret"

    with patch("src.actions.update_data.download_and_replace", return_value=headers):
        output = update_data(Params(), Mock(license_key="secret", ingest_state={}), Mock())
    assert isinstance(output, UpdateOutput)
    assert output.model_dump() == headers


def test_on_poll_creates_one_empty_container_when_database_is_current():
    with (
        patch("src.actions.on_poll.check_newer", return_value=False) as check,
        patch("src.actions.on_poll.download_and_replace") as update,
        patch.object(app.actions_manager, "save_container", return_value=(True, "saved", 42)) as save,
    ):
        result = run_action("on_poll", config={"license_key": "secret"})[-1]
    assert result.get_status()
    check.assert_called_once()
    update.assert_not_called()
    saved = save.call_args.args[0]
    assert saved["name"].startswith("maxmind_ingestion_")
    assert saved["run_automation"] is True


def test_on_poll_reports_download_failure_without_creating_container():
    with (
        patch("src.actions.on_poll.check_newer", return_value=True),
        patch("src.actions.on_poll.download_and_replace", side_effect=RuntimeError("bad%2Bkey")),
        patch.object(app.actions_manager, "save_container") as save,
    ):
        result = run_action("on_poll", config={"license_key": "bad+key"})[-1]
    assert not result.get_status()
    assert "bad%2Bkey" not in result.get_message()
    save.assert_not_called()


def test_download_replaces_database_and_records_http_last_modified(tmp_path):
    from requests.structures import CaseInsensitiveDict

    db = tmp_path / "GeoLite2-City.mmdb"
    db.write_bytes(b"old database")
    archive_bytes = io.BytesIO()
    with tarfile.open(fileobj=archive_bytes, mode="w:gz") as archive:
        payload = b"new database"
        member = tarfile.TarInfo("GeoLite2-City_20261113/GeoLite2-City.mmdb")
        member.size = len(payload)
        archive.addfile(member, io.BytesIO(payload))

    class Response:
        status_code = 200
        headers = CaseInsensitiveDict({"Last-Modified": "Fri, 13 Nov 2026 00:00:00 GMT", "Date": "Fri, 13 Nov 2026 01:00:00 GMT"})

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def iter_content(self, chunk_size):
            yield archive_bytes.getvalue()

    state = {}
    with patch("src.database.requests.get", return_value=Response()), patch("src.database.geoip2.database.Reader") as reader:
        headers = download_and_replace("secret", state, db)
    assert db.read_bytes() == b"new database"
    assert state["db_last_modified_time"] == "Fri, 13 Nov 2026 00:00:00 GMT"
    assert headers["Last-Modified"] == state["db_last_modified_time"]
    reader.assert_called_once()


def test_on_poll_propagates_container_save_failure():
    with (
        patch("src.actions.on_poll.check_newer", return_value=False),
        patch.object(app.actions_manager, "save_container", return_value=(False, "database unavailable", None)) as save,
    ):
        result = run_action("on_poll", config={"license_key": "secret"})[-1]
    assert not result.get_status()
    assert result.get_message() == "Action failure in on poll: Failed to create container: database unavailable"
    assert save.call_args.args[0]["run_automation"] is True
