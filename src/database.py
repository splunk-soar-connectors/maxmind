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

"""Read and safely update the bundled MaxMind City database."""

import ipaddress
import os
import tarfile
import tempfile
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote, quote_plus

import geoip2.database
import maxminddb
import requests
from soar_sdk.exceptions import ActionFailure


DB_PATH = Path(__file__).resolve().parents[1] / "templates" / "data" / "GeoLite2-City.mmdb"
DOWNLOAD_URL = "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key={}&suffix=tar.gz"
TIMEOUT = 30


def lookup(ip: str, db_path: Path = DB_PATH):
    try:
        reader = geoip2.database.Reader(str(db_path))
    except (OSError, maxminddb.InvalidDatabaseError) as exc:
        raise ActionFailure(f"MaxMind DB load failed for: '{db_path}': {exc}") from exc
    with reader:
        return reader.city(ip)


def license_url(key: str) -> str:
    return DOWNLOAD_URL.format(quote(key, safe=""))


def redact(message: object, key: str) -> str:
    value = str(message)
    if key:
        for secret in (key, quote(key, safe=""), quote_plus(key)):
            value = value.replace(secret, "<redacted>")
    return value


def check_newer(key: str, state: dict) -> bool:
    response = requests.head(license_url(key), timeout=TIMEOUT)
    if response.status_code != 200:
        raise ActionFailure(f"Failed to check if the database is up-to-date. Status code: {response.status_code}. Error: {response.content!r}")
    server_time = response.headers["last-modified"]
    previous_time = state.get("db_last_modified_time")
    return not previous_time or parsedate_to_datetime(server_time) > parsedate_to_datetime(previous_time)


def download_and_replace(key: str, state: dict, db_path: Path = DB_PATH) -> dict[str, str]:
    """Validate a downloaded MMDB before replacing the active file and checkpoint."""
    with requests.get(license_url(key), stream=True, timeout=TIMEOUT) as response:
        if response.status_code != 200:
            raise ActionFailure(f"Failed to download database. Status Code: {response.status_code}. Error: {response.content!r}")
        last_modified = response.headers["last-modified"]
        headers = dict(response.headers)
        with tempfile.TemporaryDirectory(dir=db_path.parent) as temporary_dir:
            archive_path = Path(temporary_dir) / "city.tar.gz"
            candidate_path = Path(temporary_dir) / db_path.name
            with archive_path.open("wb") as output:
                for chunk in response.iter_content(chunk_size=128 * 1024):
                    output.write(chunk)
            with tarfile.open(archive_path, "r:gz") as archive:
                matches = [member for member in archive.getmembers() if member.isfile() and Path(member.name).name == db_path.name]
                if len(matches) != 1:
                    raise ActionFailure("Downloaded archive must contain exactly one GeoLite2-City.mmdb file")
                member_file = archive.extractfile(matches[0])
                if member_file is None:
                    raise ActionFailure("Downloaded archive contains no readable MaxMind database")
                with member_file, candidate_path.open("wb") as output:
                    while chunk := member_file.read(128 * 1024):
                        output.write(chunk)
            with geoip2.database.Reader(str(candidate_path)):
                pass
            os.replace(candidate_path, db_path)
    state["db_last_modified_time"] = last_modified
    return headers


def validate_ip(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return False
    return True
