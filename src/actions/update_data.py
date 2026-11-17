"""Download and replace the MaxMind City database."""

from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionResult
from soar_sdk.params import Params

from ..asset import Asset
from ..database import download_and_replace, redact
from ..models import UpdateOutput


def update_data(params: Params, asset: Asset, soar: SOARClient):
    key = asset.license_key or ""
    try:
        headers = download_and_replace(key, asset.ingest_state)
    except Exception as exc:
        result = ActionResult(False, f"Error in downloading or replacing database. {redact(exc, key)}")
        result.add_data({})
        return result
    soar.set_message("Successfully updated database.")
    return UpdateOutput(**headers)
