from soar_sdk.asset import AssetField, BaseAsset


class Asset(BaseAsset):
    ip_address: str | None = AssetField(description="IP Address for testing connectivity (default: 8.8.8.8)", required=False)
    license_key: str | None = AssetField(
        description="MaxMind license key to download databases and authenticate web-service requests",
        required=False,
        sensitive=True,
    )
    account_id: str | None = AssetField(description="MaxMind account ID for live GeoIP/GeoLite web-service requests", required=False)
    web_service: str | None = AssetField(
        description="MaxMind web service used by the Make Request action",
        required=False,
        default="GeoLite",
        value_list=["GeoLite", "GeoIP"],
    )
