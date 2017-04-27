# --
# File: maxmind_consts.py
#
# Copyright (c) Phantom Cyber Corporation, 2014-2016
#
# This unpublished material is proprietary to Phantom Cyber.
# All rights reserved. The methods and
# techniques described herein are considered trade secrets
# and/or confidential. Reproduction or distribution, in whole
# or in part, is forbidden except by express written permission
# of Phantom Cyber.
#
# --


# Status/Progress Messages
MAXMIND_MSG_DB_LOAD_FAILED = "MaxMind DB load failed for: '{db_file}'"
MAXMIND_MSG_DB_LOADED = "MaxMind DB loaded"
MAXMIND_MSG_IP_NOT_FOUND = "IP '{ip}' not found"

MAXMIND_ERR_IP_NOT_FOUND = "IP not found"
MAXMIND_SUCC_IP_FOUND = "IP found"

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
