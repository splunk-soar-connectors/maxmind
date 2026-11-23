# MaxMind

Publisher: Splunk <br>
Connector Version: 2.4.2 <br>
Product Vendor: MaxMind <br>
Product Name: GeoIP2 <br>
Minimum Product Version: 7.0.0

This app provides IP geolocation with the included MaxMind database

## Getting a MaxMind license key

Navigate to [MaxMind site](https://www.maxmind.com/) > Manage License Keys > Create OR Get a
license key here

NOTE: You need to be logged in to see the option **Manage License Keys**

## Inputting Google API Key (OPTIONAL)

Navigate to Administration > Administration Settings > Google Maps. From there, insert the API
key.

This will be used to display a map widget.

## geoip2

This app makes use of the Python geoip2 module, which is licensed under the Apache 2.0 License,
Copyright (c) 2018

## POLL NOW

POLL NOW can be used to investigate what gets run on each poll during ingestion.

IMPORTANT: LicenseKey is required to be specified in your asset. It's used to fetch the latest
MaxMind database.

For more info on what gets run on each poll, see "Scheduled Polling" below.

## Scheduled Polling

This mode is used to schedule a polling action on the asset at regular intervals, which is
configured via the INGEST SETTINGS tab of the asset.

In the case of Scheduled Polling, on every poll, the app compares the timestamp of the current
database with the one on MaxMind server. The app will download the database from the server only if
the server has a newer database. With this check, the app can avoid downloading a duplicate database
and stay within the daily MaxMind download limit. As of September 14, 2021, each account can perform
up to 2,000 total downloads in each 24 hour period. For more info, visit
[here](https://support.maxmind.com/geoip-faq/databases-and-database-updates/is-there-a-limit-to-how-often-i-can-download-a-database-from-my-maxmind-account/)

The first poll after an upgrade may refresh the bundled database if its download timestamp cannot be
verified. On Poll returns poll status. Use Update Data if you need the download response headers.

It's recommended to run the database update every 30 days. The schedule of the database update can
be found
[here](https://support.maxmind.com/geoip-faq/databases-and-database-updates/how-often-should-i-purchase-geoip2-or-geoip-legacy-database-updates/)

## Make Request

Make Request sends the chosen HTTP method and relative path to the MaxMind web-service host
selected on the asset. City and Country lookups are GET examples. MaxMind determines which methods
each endpoint supports. The action requires verified TLS and returns redirect responses without
following them.

## Test Connectivity

If the connectivity IP is unset, empty, or null, the app uses `8.8.8.8`. Enter a valid IPv4 or IPv6
address to test with a different IP.

### Configuration variables

This table lists the configuration variables required to operate MaxMind. These variables are specified when configuring a GeoIP2 asset in Splunk SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**ip_address** | optional | string | IP Address for testing connectivity (default: 8.8.8.8) |
**license_key** | optional | password | MaxMind license key to download databases and authenticate web-service requests |
**account_id** | optional | string | MaxMind account ID for live GeoIP/GeoLite web-service requests |
**web_service** | optional | string | MaxMind web service used by the Make Request action |

### Supported Actions

[test connectivity](#action-test-connectivity) - test connectivity <br>
[make request](#action-make-request) - Make an authenticated request to an endpoint on the configured MaxMind host. <br>
[geolocate ip](#action-geolocate-ip) - Queries MaxMind for IP location info <br>
[update data](#action-update-data) - Update database used to locate an ip <br>
[on poll](#action-on-poll) - Update the database if there is a newer one and yield an empty container.

## action: 'test connectivity'

test connectivity

Type: **test** <br>
Read only: **True**

Basic test for app.

#### Action Parameters

No parameters are required for this action

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'make request'

Make an authenticated request to an endpoint on the configured MaxMind host.

Type: **generic** <br>
Read only: **False**

'make request' action for the app. Used to handle arbitrary HTTP requests with the app's asset

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**http_method** | required | The HTTP method to use for the request. | string | |
**endpoint** | required | Path on the configured MaxMind web-service host, for example /geoip/v2.1/city/8.8.8.8 | string | |
**headers** | optional | The headers to send with the request (JSON object). An example is {'Content-Type': 'application/json'} | string | |
**query_parameters** | optional | Parameters to append to the URL (JSON object or query string). An example is ?key=value&key2=value2 | string | |
**body** | optional | The body to send with the request (JSON object). An example is {'key': 'value', 'key2': 'value2'} | string | |
**timeout** | optional | The timeout for the request in seconds. | numeric | |
**verify_ssl** | optional | TLS certificate verification is required. Use true or omit this parameter. | boolean | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.http_method | string | | |
action_result.parameter.endpoint | string | | |
action_result.parameter.headers | string | | |
action_result.parameter.query_parameters | string | | |
action_result.parameter.body | string | | |
action_result.parameter.timeout | numeric | | |
action_result.parameter.verify_ssl | boolean | | |
action_result.data.\*.status_code | numeric | | 200 404 500 |
action_result.data.\*.response_body | string | | {"key": "value"} |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'geolocate ip'

Queries MaxMind for IP location info

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**ip** | required | IP (IPv4/IPv6) to geolocate | string | `ip` `ipv6` |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.ip | string | `ip` `ipv6` | |
action_result.data.\*.city_name | string | | Ahmedabad |
action_result.data.\*.state_name | string | | Gujarat |
action_result.data.\*.state_iso_code | string | | GJ |
action_result.data.\*.country_name | string | | India |
action_result.data.\*.country_iso_code | string | | IN |
action_result.data.\*.continent_name | string | | Asia |
action_result.data.\*.latitude | numeric | | 23.0333 |
action_result.data.\*.longitude | numeric | | 72.6167 |
action_result.data.\*.time_zone | string | | Asia/Kolkata |
action_result.data.\*.postal_code | string | | 380007 |
action_result.data.\*.as_number | numeric | | |
action_result.data.\*.as_org | string | | |
action_result.data.\*.domain | string | | |
action_result.summary.city | string | | |
action_result.summary.state | string | | |
action_result.summary.country | string | | |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'update data'

Update database used to locate an ip

Type: **generic** <br>
Read only: **False**

This app uses the MaxMind GeoLite2 City database.

#### Action Parameters

No parameters are required for this action

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.data.\*.Date | string | | |
action_result.data.\*.ETag | string | | |
action_result.data.\*.Expires | string | | |
action_result.data.\*.Last-Modified | string | | |
action_result.data.\*.Content-Type | string | | |
action_result.data.\*.Content-Length | string | | |
action_result.data.\*.Vary | string | | |
action_result.data.\*.CF-Ray | string | | |
action_result.data.\*.Server | string | | |
action_result.data.\*.expect-ct | string | | |
action_result.data.\*.Connection | string | | |
action_result.data.\*.Accept-Ranges | string | | |
action_result.data.\*.Cache-Control | string | | |
action_result.data.\*.CF-Cache-Status | string | | |
action_result.data.\*.X-MaxMind-Worker | string | | |
action_result.data.\*.Content-Disposition | string | | |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'on poll'

Update the database if there is a newer one and yield an empty container.

Type: **ingest** <br>
Read only: **True**

Callback action for the on_poll ingest functionality

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**start_time** | optional | Start of time range, in epoch time (milliseconds). | numeric | |
**end_time** | optional | End of time range, in epoch time (milliseconds). | numeric | |
**container_count** | optional | Maximum number of container records to query for. | numeric | |
**artifact_count** | optional | Maximum number of artifact records to query for. | numeric | |
**container_id** | optional | Comma-separated list of container IDs to limit the ingestion to. | string | |

#### Action Output

No Output

______________________________________________________________________

Auto-generated Splunk SOAR Connector documentation.

Copyright 2026 Splunk Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.
