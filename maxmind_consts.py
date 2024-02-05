# File: maxmind_consts.py
#
# Copyright (c) 2016-2024 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions
# and limitations under the License.
#
#
# Status/Progress Messages
MAXMIND_MSG_DB_LOAD_FAILED = "MaxMind DB load failed for: '{db_file}'"
MAXMIND_MSG_DB_LOADED = "MaxMind DB loaded"
MAXMIND_MSG_IP_NOT_FOUND = "IP '{ip}' not found"
MAXMIND_SUCCESS_MSG_IP_NOT_FOUND = "Successfully able to query the MaxMind DB for the IP: '{ip}'. But, the requested IP not found."
MAXMIND_SUCCESS_MSG_IP_FOUND = "Successfully able to query the MaxMind DB for the IP: '{ip}'"

MAXMIND_ERR_IP_NOT_FOUND = "IP not found"
MAXMIND_DEFAULT_IP_CONNECTIVITY = "8.8.8.8"

# Jsons used either in params or result
MAXMIND_JSON_CITY_NAME = "city_name"
MAXMIND_JSON_STATE_NAME = "state_name"
MAXMIND_JSON_STATE_ISO_CODE = "state_iso_code"
MAXMIND_JSON_COUNTRY_NAME = "country_name"
MAXMIND_JSON_COUNTRY_ISO_CODE = "country_iso_code"
MAXMIND_JSON_CONTINENT_NAME = "continent_name"
MAXMIND_JSON_LATITUDE = "latitude"
MAXMIND_JSON_LONGITUDE = "longitude"
MAXMIND_JSON_TIME_ZONE = "time_zone"
MAXMIND_JSON_AS_NUMBER = "as_number"
MAXMIND_JSON_AS_ORG = "as_org"
MAXMIND_JSON_DOMAIN = "domain"
MAXMIND_JSON_POSTAL_CODE = "postal_code"
MAXMIND_JSON_CITY = "city"
MAXMIND_JSON_STATE = "state"
MAXMIND_JSON_COUNTRY = "country"

# Other constants used in the connector
MMDB_FILE = "GeoLite2-City.mmdb"
MMDB_TAR_FILE = "GeoLite2-City.tar.gz"
DB_DOWNLOAD_URL = "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key={0}&suffix=tar.gz"

DEFAULT_REQUEST_TIMEOUT = 30  # in seconds
