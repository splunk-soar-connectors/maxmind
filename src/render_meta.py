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

"""Preserve legacy widget metadata not exposed by the SDK metadata model."""

from soar_sdk.meta.actions import ActionMeta


class MapActionMeta(ActionMeta):
    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        data["render"] = {"type": "map", "width": 10, "height": 5, "title": "IP Geolocation"}
        mapping = {
            "country_name": "Country",
            "latitude": "latitude",
            "longitude": "longitude",
            "city_name": "City",
            "postal_code": "Postal Code",
            "as_org": "Organization",
            "state_name": "State/Province",
        }
        for field in data["output"]:
            name = field["data_path"].removeprefix("action_result.data.*.")
            if name in mapping:
                field["map_info"] = mapping[name]
            if field["data_path"] == "action_result.parameter.ip":
                field["map_info"] = "name"
        return data


class UpdateTableActionMeta(ActionMeta):
    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        data["render"] = {"type": "table", "width": 12, "height": 5, "title": "Update Database"}
        columns = {"action_result.status": ("Status", 0), "action_result.message": ("Message", 1)}
        for field in data["output"]:
            if field["data_path"] in columns:
                field["column_name"], field["column_order"] = columns[field["data_path"]]
        return data


def preserve_render_metadata(app) -> None:
    for identifier, meta_class in (("lookup_ip", MapActionMeta), ("update_database", UpdateTableActionMeta)):
        action = app.actions_manager.get_action(identifier)
        # Copy model fields before serialization so the parameter and output classes stay intact.
        action.meta = meta_class(**vars(action.meta))
