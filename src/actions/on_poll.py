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

"""Refresh the MaxMind City database and yield one empty ingested container."""

from collections.abc import Iterator
from datetime import UTC, datetime

from soar_sdk.exceptions import ActionFailure
from soar_sdk.logging import getLogger
from soar_sdk.models.container import Container
from soar_sdk.params import MAX_COUNT_VALUE, OnPollParams

from ..asset import Asset
from ..database import check_newer, download_and_replace, redact


logger = getLogger()


def run_on_poll(params: OnPollParams, asset: Asset) -> Iterator[Container]:
    key = asset.license_key or ""
    if not key:
        raise ActionFailure("License key is required to fetch MaxMind database.")
    state = asset.ingest_state
    if "db_last_modified_time" not in state:
        legacy = state.backend.load_state() or {}
        if legacy.get("db_last_modified_time"):
            state["db_last_modified_time"] = legacy["db_last_modified_time"]
    try:
        if check_newer(key, state):
            download_and_replace(key, state)
            if params.container_count and int(params.container_count) != MAX_COUNT_VALUE:
                logger.progress("Successfully updated the database to the latest version")
        else:
            logger.progress("The database is already up to date.")
    except Exception as exc:
        raise ActionFailure(f"Failed to poll. Reason: {redact(exc, key)}") from exc
    name = f"maxmind_ingestion_{datetime.now(UTC):%Y-%m-%dT%H:%M:%SZ}"
    yield Container(name=name, run_automation=True)
