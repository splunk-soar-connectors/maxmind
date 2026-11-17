**Unreleased**

* Converted the connector to the Splunk SOAR SDK. Requires Splunk SOAR 7.0.0 and Python 3.13.
* Database updates now validate the downloaded file before replacing the active database. An invalid download leaves the existing database in place.
* The geolocate IP action now publishes its existing `as_number` and `domain` result fields as output paths.
* Removed the unused `update data` summary output path from the app metadata; response headers and the action message are unchanged.
* Test Connectivity uses the SDK action identifier `test_connectivity` (previously `test_asset_connectivity`); On Poll now exposes standard status, message, and parameter paths.
* Added Make Request for live MaxMind GeoIP and GeoLite lookups. It requires an account ID and license key, and uses the selected web-service plan.
* Test Connectivity now validates the configured live GeoIP or GeoLite web-service credentials when both an account ID and license key are present.
