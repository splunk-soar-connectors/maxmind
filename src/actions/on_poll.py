"""Refresh the MaxMind City database and create one empty ingested container."""

from datetime import UTC, datetime

from soar_sdk.action_results import ActionResult
from soar_sdk.app import App
from soar_sdk.logging import getLogger
from soar_sdk.params import MAX_COUNT_VALUE, Param, Params

from ..asset import Asset
from ..database import check_newer, download_and_replace, redact


logger = getLogger()


class PollParams(Params):
    container_id: str | None = Param(description="Container IDs to limit the ingestion to", required=False)
    start_time: float | None = Param(description="Start of time range, in epoch time (milliseconds)", required=False)
    end_time: float | None = Param(description="End of time range, in epoch time (milliseconds)", required=False)
    container_count: float | None = Param(description="Maximum number of container records to query for", required=False)
    artifact_count: float | None = Param(description="Maximum number of artifact records to query for", required=False)


def run_on_poll(params: PollParams, asset: Asset, app: App) -> ActionResult:
    key = asset.license_key or ""
    if not key:
        return ActionResult(False, "License key is required to fetch MaxMind database.")
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
        return ActionResult(False, f"Failed to poll. Reason: {redact(exc, key)}")
    name = f"maxmind_ingestion_{datetime.now(UTC):%Y-%m-%dT%H:%M:%SZ}"
    # Keep the key absent, as in the legacy save_container call. SOAR decides when to run automation.
    success, message, _container_id = app.actions_manager.save_container({"name": name})
    # Polling has no output row; preserve the container save status and message.
    return ActionResult(bool(success), message)
