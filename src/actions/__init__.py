"""Register MaxMind actions."""

from soar_sdk.action_results import ActionOutput
from soar_sdk.app import App

from ..asset import Asset
from ..models import GeoOutput, GeoSummary, UpdateOutput
from ..render_meta import preserve_render_metadata
from .geolocate_ip import GeolocateIpParams, geolocate_ip
from .make_request import make_request
from .on_poll import PollParams, run_on_poll
from .update_data import update_data


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

    def on_poll(params: PollParams, asset: Asset):
        return run_on_poll(params, asset, app)

    app.register_action(
        action=on_poll,
        name="on poll",
        identifier="on_poll",
        description="Update the database if there is a newer one on the server",
        verbose="This action replaces the maxmind database if database is updated.",
        action_type="ingest",
        read_only=True,
        params_class=PollParams,
        output_class=ActionOutput,
    )
    preserve_render_metadata(app)
    return app
