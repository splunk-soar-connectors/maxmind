**Unreleased**

* Converted the connector to the Splunk SOAR SDK. Requires Splunk SOAR 7.0.0 and Python 3.13.
* Test Connectivity changed from `test_asset_connectivity` to `test_connectivity`. Update callers that use the action identifier.
* On Poll no longer returns download headers in the raw action result. Use Update Data to retrieve them.
* Added Make Request for live MaxMind GeoIP and GeoLite lookups. It requires an account ID and license key, and uses the selected web-service plan.
* Test Connectivity now validates the configured live GeoIP or GeoLite web-service credentials when both an account ID and license key are present.
