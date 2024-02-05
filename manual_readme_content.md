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
