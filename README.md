[comment]: # "Auto-generated SOAR connector documentation"
# MaxMind

Publisher: Splunk  
Connector Version: 2\.2\.5  
Product Vendor: MaxMind  
Product Name: GeoIP2  
Product Version Supported (regex): "\.\*"  
Minimum Product Version: 5\.0\.0  

This app provides IP geolocation with the included MaxMind database

[comment]: # " File: README.md"
[comment]: # "Copyright (c) 2016-2020 Splunk Inc."
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
**ip\_address** |  optional  | string | IP Address for testing connectivity \(default\: 8\.8\.8\.8\)
**license\_key** |  optional  | password | MaxMind License key to download new databases

### Supported Actions  
[test connectivity](#action-test-connectivity) - Validate the asset configuration for connectivity\. This action queries the MaxMind DB for the IP mentioned in the configuration parameters  
[geolocate ip](#action-geolocate-ip) - Queries MaxMind for IP location info  
[update data](#action-update-data) - Update database used to locate an ip  
[on poll](#action-on-poll) - Update the database if there is a newer one on the server  

## action: 'test connectivity'
Validate the asset configuration for connectivity\. This action queries the MaxMind DB for the IP mentioned in the configuration parameters

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
**ip** |  required  | IP to geolocate | string |  `ip` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.data\.\*\.continent\_name | string | 
action\_result\.data\.\*\.country\_iso\_code | string | 
action\_result\.data\.\*\.country\_name | string | 
action\_result\.data\.\*\.latitude | numeric | 
action\_result\.data\.\*\.longitude | numeric | 
action\_result\.parameter\.ip | string |  `ip` 
action\_result\.parameter\.ip | string |  `ip` 
action\_result\.data\.\*\.city\_name | string | 
action\_result\.data\.\*\.postal\_code | string | 
action\_result\.data\.\*\.as\_org | string | 
action\_result\.data\.\*\.state\_iso\_code | string | 
action\_result\.data\.\*\.state\_name | string | 
action\_result\.data\.\*\.time\_zone | string | 
action\_result\.summary\.city | string | 
action\_result\.summary\.state | string | 
action\_result\.summary\.country | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'update data'
Update database used to locate an ip

Type: **generic**  
Read only: **False**

This app uses the MaxMind GeoLite2 City database\.

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.data\.\*\.Date | string | 
action\_result\.data\.\*\.ETag | string | 
action\_result\.data\.\*\.Vary | string | 
action\_result\.data\.\*\.CF\-Ray | string | 
action\_result\.data\.\*\.Server | string | 
action\_result\.data\.\*\.Expires | string | 
action\_result\.data\.\*\.expect\-ct | string | 
action\_result\.data\.\*\.Connection | string | 
action\_result\.data\.\*\.Content\-Type | string | 
action\_result\.data\.\*\.Accept\-Ranges | string | 
action\_result\.data\.\*\.Cache\-Control | string | 
action\_result\.data\.\*\.Last\-Modified | string | 
action\_result\.data\.\*\.Content\-Length | string | 
action\_result\.data\.\*\.CF\-Cache\-Status | string | 
action\_result\.data\.\*\.X\-MaxMind\-Worker | string | 
action\_result\.data\.\*\.Content\-Disposition | string | 
action\_result\.message | string | 
action\_result\.summary | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'on poll'
Update the database if there is a newer one on the server

Type: **ingest**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**container\_id** |  optional  | Container IDs to limit the ingestion to | string | 
**start\_time** |  optional  | Start of time range, in epoch time \(milliseconds\) | numeric | 
**end\_time** |  optional  | End of time range, in epoch time \(milliseconds\) | numeric | 
**container\_count** |  optional  | Maximum number of container records to query for | numeric | 
**artifact\_count** |  optional  | Maximum number of artifact records to query for | numeric | 

#### Action Output
No Output