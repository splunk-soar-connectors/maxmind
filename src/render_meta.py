"""Preserve legacy widget metadata not exposed by SDK 7.1.3."""

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
        return data


def preserve_render_metadata(app) -> None:
    # Pydantic creates model_fields dynamically; getattr keeps static analysis accurate.
    field_names = getattr(ActionMeta, "model_fields")
    for identifier, meta_class in (("lookup_ip", MapActionMeta), ("update_database", UpdateTableActionMeta)):
        action = app.actions_manager.get_action(identifier)
        values = {name: getattr(action.meta, name) for name in field_names}
        action.meta = meta_class(**values)
