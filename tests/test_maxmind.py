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
from functools import partial
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from requests.structures import CaseInsensitiveDict
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Params
from soar_sdk.shims.phantom.encryption_helper import encryption_helper

from src.actions.geolocate_ip import GeolocateIpParams, GeoOutput, geolocate_ip
from src.actions.make_request import MaxMindMakeRequestParams, make_request
from src.actions.update_data import UpdateOutput, update_data
from src.app import app
from src.asset import Asset
from src.database import check_newer, download_and_replace, lookup


def run_action(identifier, params=None, config=None, *, parameter_rows=None):
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
                "parameters": parameter_rows if parameter_rows is not None else [params or {}],
            }
        )
    )
    return app.actions_manager.get_results()


def test_geolocate_multiple_ips_keeps_individual_metadata():
    results = run_action("lookup_ip", {"ip": "8.8.8.8, 255.255.255.255"})
    assert len(results) == 2
    assert all(result.get_status() for result in results)
    assert results[0].get_data()[0]["country_iso_code"] == "US"
    assert "latitude" in results[0].get_data()[0]
    assert results[0].get_param()["ip"] == "8.8.8.8"
    assert results[0].get_summary()["country"] == "United States"
    assert results[1].get_param()["ip"] == "255.255.255.255"
    assert results[1].get_summary() == {}
    assert results[1].get_message() == "IP not found"
    assert results[1].get_data() == [{}]


@pytest.mark.parametrize("ip", ["8.8.8.8,8.8.8.8", "8.8.8.8, 8.8.8.8"])
def test_geolocate_duplicate_ips_returns_one_result(ip):
    with patch("src.actions.geolocate_ip.lookup", wraps=lookup) as lookup_mock:
        results = run_action("lookup_ip", {"ip": ip})

    assert len(results) == 1
    assert results[0].get_status()
    assert results[0].get_param()["ip"] == "8.8.8.8"
    lookup_mock.assert_called_once_with("8.8.8.8")


def test_single_ip_returns_declared_model_without_missing_fields():
    output = geolocate_ip(GeolocateIpParams(ip="8.8.8.8"), Mock())
    assert isinstance(output, GeoOutput)
    assert output.model_dump()["country_iso_code"] == "US"
    assert None not in output.model_dump().values()

    result = run_action("lookup_ip", {"ip": "8.8.8.8"})[-1]
    assert result.get_data() == [output.model_dump()]
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


def test_geolocate_separate_parameter_rows_do_not_share_metadata():
    results = run_action("lookup_ip", parameter_rows=[{"ip": ip} for ip in ("8.8.8.8", "255.255.255.255", "1.1.1.1")])
    assert results[0].get_summary()["country"] == "United States"
    assert results[1].get_summary() == {}
    assert results[1].get_message() == "IP not found"
    assert results[2].get_summary()["country"] == "Australia"
    assert results[2].get_message() != "IP not found"


@pytest.mark.parametrize("bad_lookup", [RuntimeError("lookup failed"), SimpleNamespace(city=SimpleNamespace(name=[]))])
def test_geolocate_batch_keeps_completed_rows_after_an_error(bad_lookup):
    with patch("src.actions.geolocate_ip.lookup", side_effect=[lookup("8.8.8.8"), bad_lookup, lookup("1.1.1.1")]):
        results = run_action("lookup_ip", {"ip": "8.8.8.8,9.9.9.9,1.1.1.1"})
    assert [result.get_status() for result in results] == [True, False, True]
    assert results[1].get_param()["ip"] == "9.9.9.9"
    assert "Failed to geolocate IP 9.9.9.9" in results[1].get_message()
    assert results[0].get_data()[0]["country_iso_code"] == "US"
    assert results[2].get_data()[0]["country_iso_code"] == "AU"


def test_geolocate_preserves_legacy_sparse_fields():
    class Subdivisions(list):
        @property
        def most_specific(self):
            return self[0]

    response = SimpleNamespace(
        country=SimpleNamespace(name=None, iso_code="US"),
        subdivisions=Subdivisions([SimpleNamespace(name=None, iso_code=None)]),
    )
    with patch("src.actions.geolocate_ip.lookup", return_value=response):
        result = run_action("lookup_ip", {"ip": "8.8.8.8"})[0]
    assert result.get_data() == [{"state_name": None, "state_iso_code": None}]
    assert result.get_summary() == {"state": None}


def test_connectivity_accepts_valid_ip_and_rejects_bad_asset_ip():
    assert run_action("test_connectivity", config={"ip_address": "255.255.255.255"})[-1].get_status()
    assert not run_action("test_connectivity", config={"ip_address": "invalid"})[-1].get_status()


@pytest.mark.parametrize("config", [{}, {"ip_address": ""}, {"ip_address": None}])
def test_connectivity_defaults_unset_ip(config):
    with patch("src.test_connectivity.lookup") as reader:
        result = run_action("test_connectivity", config=config)[-1]
    assert result.get_status()
    reader.assert_called_once_with("8.8.8.8")


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
    with patch("src.actions.make_request.requests.request", return_value=response) as request:
        output = make_request(params, asset)
    assert output.status_code == 200
    assert output.response_body == response.text
    assert request.call_args.kwargs["url"] == "https://geolite.info/geoip/v2.1/city/8.8.8.8"
    assert request.call_args.kwargs["method"] == "GET"
    assert request.call_args.kwargs["auth"] == ("123", "secret")
    assert request.call_args.kwargs["headers"] == {"Accept": "application/json", "Accept-Language": "en"}
    assert request.call_args.kwargs["params"] == {"pretty": "true"}


def test_make_request_returns_api_errors_as_response_data():
    response = Mock(status_code=401, text='{"code": "AUTHORIZATION_INVALID"}')
    with patch("src.actions.make_request.requests.request", return_value=response):
        result = run_action(
            "make_request",
            {"http_method": "GET", "endpoint": "/geoip/v2.1/country/8.8.8.8"},
            {"account_id": "123", "license_key": "secret"},
        )[-1]
    assert result.get_status()
    assert result.get_data() == [{"status_code": 401, "response_body": response.text}]


def test_make_request_requires_verified_tls_before_sending_credentials():
    with patch("src.actions.make_request.requests.request") as request:
        result = run_action(
            "make_request",
            {"http_method": "GET", "endpoint": "/geoip/v2.1/country/8.8.8.8", "verify_ssl": False},
            {"account_id": "123", "license_key": "secret"},
        )[-1]
    assert not result.get_status()
    assert "TLS certificate verification is required" in result.get_message()
    request.assert_not_called()


@pytest.mark.parametrize(
    "params, asset",
    [
        (
            MaxMindMakeRequestParams(http_method="GET", endpoint="https://geolite.info/geoip/v2.1/city/8.8.8.8"),
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


def test_make_request_passes_arbitrary_method_endpoint_and_body_to_configured_host():
    response = Mock(status_code=202, text='{"accepted": true}')
    params = MaxMindMakeRequestParams(
        http_method="POST",
        endpoint="/future/api/v3/lookup",
        headers='{"Content-Type": "application/json"}',
        query_parameters="mode=bulk",
        body='{"ips": ["8.8.8.8", "1.1.1.1"]}',
    )
    with patch("src.actions.make_request.requests.request", return_value=response) as request:
        output = make_request(params, Asset(account_id="123", license_key="secret", web_service="GeoLite"))
    assert output.status_code == 202
    assert request.call_args.kwargs == {
        "method": "POST",
        "url": "https://geolite.info/future/api/v3/lookup",
        "auth": ("123", "secret"),
        "headers": {"Accept": "application/json", "Content-Type": "application/json"},
        "params": "mode=bulk",
        "data": '{"ips": ["8.8.8.8", "1.1.1.1"]}',
        "timeout": 30,
        "allow_redirects": False,
    }


def test_poll_requires_license_key():
    result = run_action("on_poll")[-1]
    assert not result.get_status()
    assert "License key is required" in result.get_message()


def test_poll_does_not_trust_legacy_checkpoint_without_a_matching_database(tmp_path):
    db = tmp_path / "GeoLite2-City.mmdb"
    db.write_bytes(b"bundled database")
    last_modified = "Tue, 02 Jan 2024 00:00:00 GMT"
    state = {"db_last_modified_time": last_modified}
    response = Mock(status_code=200, headers={"last-modified": last_modified})
    with (
        patch.object(app.actions_manager, "load_state", return_value=state),
        patch("src.database.requests.head", return_value=response) as head,
        patch("src.actions.on_poll.check_newer", partial(check_newer, db_path=db)),
        patch("src.actions.on_poll.download_and_replace") as update,
        patch.object(app.actions_manager, "save_container", return_value=(True, "saved", 42)) as save,
    ):
        result = run_action("on_poll", config={"license_key": "secret"})[-1]
    assert result.get_status()
    assert head.call_args.kwargs["allow_redirects"] is True
    update.assert_called_once_with("secret")
    assert save.call_args.args[0]["run_automation"] is False


def test_update_failure_redacts_license_key():
    with patch("src.actions.update_data.download_and_replace", side_effect=RuntimeError("https://example/?license_key=bad%2Bkey")):
        result = run_action("update_database", config={"license_key": "bad+key"})[-1]
    assert not result.get_status()
    assert "bad+key" not in result.get_message()
    assert "bad%2Bkey" not in result.get_message()


@pytest.mark.parametrize("config", [{}, {"license_key": "  "}])
def test_update_data_rejects_missing_key_without_downloading(config):
    with patch("src.actions.update_data.download_and_replace") as update:
        result = run_action("update_database", config=config)[-1]
    assert not result.get_status()
    assert "License key is required to fetch MaxMind database." in result.get_message()
    assert result.get_data() == [{}]
    update.assert_not_called()


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

    with patch("src.database.requests.get", return_value=Response()), pytest.raises(Exception):
        download_and_replace("secret", db)
    assert db.read_bytes() == b"old data"
    assert list(tmp_path.iterdir()) == [db]


def test_manifest_keeps_map_and_documented_output_paths():
    geolocate = app.actions_manager.get_action("lookup_ip").meta.model_dump()
    assert geolocate["render"] == {"type": "map", "width": 10, "height": 5, "title": "IP Geolocation"}
    update = app.actions_manager.get_action("update_database").meta.model_dump()
    assert update["render"] == {"type": "table", "width": 12, "height": 5, "title": "Update Database"}
    assert [(field["column_name"], field["column_order"]) for field in update["output"] if "column_order" in field] == [
        ("Status", 0),
        ("Message", 1),
    ]
    paths = {field["data_path"] for field in geolocate["output"]}
    assert {"action_result.data.*.latitude", "action_result.data.*.longitude", "action_result.summary.country"} <= paths
    assert next(field for field in geolocate["output"] if field["data_path"] == "action_result.parameter.ip")["map_info"] == "name"


def test_update_data_returns_response_headers():
    headers = {
        "Date": "Mon, 03 Jan 2022 19:37:02 GMT",
        "Last-Modified": "Tue, 28 Dec 2021 17:52:24 GMT",
        "Expires": "Mon, 03 Jan 2022 19:37:02 GMT",
    }
    with (
        patch("src.actions.update_data.download_and_replace", return_value=headers) as update,
        patch.object(app.actions_manager, "save_state", return_value=False) as save_state,
    ):
        result = run_action("update_database", config={"license_key": "secret"})[-1]
    assert result.get_status()
    assert result.get_message() == "Successfully updated database."
    assert result.get_data() == [headers]
    update.assert_called_once_with("secret")
    save_state.assert_not_called()

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
    assert saved["run_automation"] is False


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


@pytest.fixture
def downloaded_database():
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

    return Response()


def test_download_rejects_readable_wrong_edition(tmp_path, downloaded_database):
    db = tmp_path / "GeoLite2-City.mmdb"
    db.write_bytes(b"old database")
    with (
        patch("src.database.requests.get", return_value=downloaded_database),
        patch("src.database.geoip2.database.Reader") as reader,
        pytest.raises(ActionFailure, match="not a GeoLite2-City database"),
    ):
        reader.return_value.__enter__.return_value.metadata.return_value.database_type = "GeoLite2-Country"
        download_and_replace("secret", db)
    assert db.read_bytes() == b"old database"
    assert list(tmp_path.iterdir()) == [db]


def test_on_poll_retry_uses_installed_database_after_container_save_fails(tmp_path, downloaded_database):
    db = tmp_path / "GeoLite2-City.mmdb"
    db.write_bytes(b"old database")
    with (
        patch("src.database.requests.head", return_value=downloaded_database),
        patch("src.database.requests.get", return_value=downloaded_database) as get,
        patch("src.database.geoip2.database.Reader") as reader,
        patch("src.actions.on_poll.check_newer", partial(check_newer, db_path=db)),
        patch("src.actions.on_poll.download_and_replace", partial(download_and_replace, db_path=db)),
        patch.object(app.actions_manager, "save_container", side_effect=[(False, "database unavailable", None), (True, "saved", 42)]) as save,
    ):
        reader.return_value.__enter__.return_value.metadata.return_value.database_type = "GeoLite2-City"
        failed = run_action("on_poll", config={"license_key": "secret"})[-1]
        assert not failed.get_status()
        assert "Failed to create container: database unavailable" in failed.get_message()
        assert db.read_bytes() == b"new database"
        assert run_action("on_poll", config={"license_key": "secret"})[-1].get_status()
        get.assert_called_once()
        assert not check_newer("secret", db)
        db.write_bytes(b"replacement database")
        assert check_newer("secret", db)
    assert all(call.args[0]["run_automation"] is False for call in save.call_args_list)
