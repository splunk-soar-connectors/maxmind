[comment]: # "Auto-generated SOAR connector documentation"
# MaxMind

Publisher: Splunk  
Connector Version: 2.3.1  
Product Vendor: MaxMind  
Product Name: GeoIP2  
Product Version Supported (regex): ".\*"  
Minimum Product Version: 6.2.1  

This app provides IP geolocation with the included MaxMind database

[comment]: # " File: README.md"
[comment]: # "Copyright (c) 2016-2024 Splunk Inc."
[comment]: # ""
[comment]: # "Licensed under the Apache License, Version 2.0 (the 'License');"
[comment]: # "you may not use this file except in compliance with the License."
[comment]: # "You may obtain a copy of the License at"
[comment]: # ""
[comment]: # "    http://www.apache.org/licenses/LICENSE-2.0"
[comment]: # ""
[comment]: # "Unless required by applicable law or agreed to in writing, software distributed under"
[comment]: # "the License is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,"
[comment]: # "either express or implied. See the License for the specific language governing permissions"
[comment]: # "and limitations under the License."
[comment]: # ""
## Getting a MaxMind license key

Navigate to [MaxMind site](https://www.maxmind.com/) \> Manage License Keys \> Create OR Get a
license key here

NOTE: You need to be logged in to see the option **Manage License Keys**

## Inputting Google API Key (OPTIONAL)

Navigate to Administration \> Administration Settings \> Google Maps. From there, insert the API
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

It's recommended to run the database update every 30 days. The schedule of the database update can
be found
[here](https://support.maxmind.com/geoip-faq/databases-and-database-updates/how-often-should-i-purchase-geoip2-or-geoip-legacy-database-updates/)


### Configuration Variables
The below configuration variables are required for this Connector to operate.  These variables are specified when configuring a GeoIP2 asset in SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**ip_address** |  optional  | string | IP Address for testing connectivity (default: 8.8.8.8)
**license_key** |  optional  | password | MaxMind License key to download new databases

### Supported Actions  
[test connectivity](#action-test-connectivity) - Validate the asset configuration for connectivity. This action queries the MaxMind DB for the IP mentioned in the configuration parameters  
[geolocate ip](#action-geolocate-ip) - Queries MaxMind for IP location info  
[update data](#action-update-data) - Update database used to locate an ip  
[on poll](#action-on-poll) - Update the database if there is a newer one on the server  

## action: 'test connectivity'
Validate the asset configuration for connectivity. This action queries the MaxMind DB for the IP mentioned in the configuration parameters

Type: **test**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
No Output  

## action: 'geolocate ip'
Queries MaxMind for IP location info

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**ip** |  required  | IP (IPv4/IPv6) to geolocate | string |  `ip`  `ipv6` 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.data.\*.continent_name | string |  |   Asia 
action_result.data.\*.country_iso_code | string |  |   IN 
action_result.data.\*.country_name | string |  |   India 
action_result.data.\*.latitude | numeric |  |   23.0333 
action_result.data.\*.longitude | numeric |  |   72.6167 
action_result.parameter.ip | string |  `ip`  `ipv6`  |   203.88.139.34 
action_result.data.\*.city_name | string |  |   Ahmedabad 
action_result.data.\*.postal_code | string |  |   380007 
action_result.data.\*.as_org | string |  |  
action_result.data.\*.state_iso_code | string |  |   GJ 
action_result.data.\*.state_name | string |  |   Gujarat 
action_result.data.\*.time_zone | string |  |   Asia/Kolkata 
action_result.summary.city | string |  |   Ahmedabad 
action_result.summary.state | string |  |   GJ 
action_result.summary.country | string |  |   India 
action_result.message | string |  |   City: Ahmedabad, State: GJ, Country: India 
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1   

## action: 'update data'
Update database used to locate an ip

Type: **generic**  
Read only: **False**

This app uses the MaxMind GeoLite2 City database.

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |   success  failed 
action_result.data.\*.Date | string |  |   Mon, 03 Jan 2022 19:37:02 GMT 
action_result.data.\*.ETag | string |  |   a3fd54f5dae1d3760e32ee743e21ffbc 
action_result.data.\*.Vary | string |  |   Accept-Encoding 
action_result.data.\*.CF-Ray | string |  |   6c7eadeaee340899-SEA 
action_result.data.\*.Server | string |  |   cloudflare 
action_result.data.\*.Expires | string |  |   Mon, 03 Jan 2022 19:37:02 GMT 
action_result.data.\*.expect-ct | string |  |   max-age=604800, report-uri="https://report-uri.cloudflare.com/cdn-cgi/beacon/expect-ct" 
action_result.data.\*.Connection | string |  |   keep-alive 
action_result.data.\*.Content-Type | string |  |   application/gzip 
action_result.data.\*.Accept-Ranges | string |  |   bytes 
action_result.data.\*.Cache-Control | string |  |   private, max-age=0 
action_result.data.\*.Last-Modified | string |  |   Tue, 28 Dec 2021 17:52:24 GMT 
action_result.data.\*.Content-Length | string |  |   35748628 
action_result.data.\*.CF-Cache-Status | string |  |   DYNAMIC 
action_result.data.\*.X-MaxMind-Worker | string |  |   enabled 
action_result.data.\*.Content-Disposition | string |  |   attachment; filename=GeoLite2-City_20211228.tar.gz 
action_result.message | string |  |   Successfully updated database. 
action_result.summary | string |  |  
summary.total_objects | numeric |  |   1 
summary.total_objects_successful | numeric |  |   1   

## action: 'on poll'
Update the database if there is a newer one on the server

Type: **ingest**  
Read only: **True**

This action replaces the maxmind database if database is updated.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**container_id** |  optional  | Container IDs to limit the ingestion to | string | 
**start_time** |  optional  | Start of time range, in epoch time (milliseconds) | numeric | 
**end_time** |  optional  | End of time range, in epoch time (milliseconds) | numeric | 
**container_count** |  optional  | Maximum number of container records to query for | numeric | 
**artifact_count** |  optional  | Maximum number of artifact records to query for | numeric | 

#### Action Output
No Output