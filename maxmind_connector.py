# File: maxmind_connector.py
# Copyright (c) 2016-2019 Splunk Inc.
#
# SPLUNK CONFIDENTIAL - Use or disclosure of this material in whole or in part
# without a valid written license from Splunk Inc. is PROHIBITED.

import os

# Phantom imports
import phantom.app as phantom
from phantom.base_connector import BaseConnector
from phantom.action_result import ActionResult

# THIS Connector imports
from maxmind_consts import *

import geoip2.database

MMDB_FILE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), MMDB_FILE)


class MaxmindConnector(BaseConnector):

    # Commands supported by this script
    ACTION_ID_LOOKUP_IP_GEO_LOCATION = "lookup_ip"

    def __init__(self):

        # Call the BaseConnectors init first
        super(MaxmindConnector, self).__init__()

        self.reader = None

    def initialize(self):

        # Load the country db
        try:
            self.reader = geoip2.database.Reader(MMDB_FILE_PATH)
        except Exception as e:
            self.save_progress(MAXMIND_MSG_DB_LOAD_FAILED, db_file=MMDB_FILE_PATH)
            return self.set_status(phantom.APP_ERROR, MAXMIND_MSG_DB_LOAD_FAILED, e, db_file=MMDB_FILE_PATH)

        self.save_progress(MAXMIND_MSG_DB_LOADED)
        return phantom.APP_SUCCESS

    def _handle_lookup_ip_list(self, param):

        ip_list_conf = phantom.get_req_value(param, phantom.APP_JSON_IP)
        ip_list = phantom.get_list_from_string(ip_list_conf)

        for ip in ip_list:

            # Create a ActionResult object to store the result
            action_result = self.add_action_result(ActionResult({phantom.APP_JSON_IP: ip}))

            # Add the data that will store the details of this command
            curr_data = action_result.add_data({})

            try:
                city_details = self.reader.city(ip)
            except:
                self.save_progress(MAXMIND_MSG_IP_NOT_FOUND, ip=ip)
                action_result.set_status(phantom.APP_SUCCESS, MAXMIND_ERR_IP_NOT_FOUND, ip=ip)
                continue

            # Found the IP
            action_result.set_status(phantom.APP_SUCCESS)

            checkattr = lambda x, y: (hasattr(x, y) and (getattr(x, y) is not None))

            # Now parse the result to normalize into the result
            if (checkattr(city_details, 'city') and checkattr(city_details.city, 'name')):
                curr_data[MAXMIND_JSON_CITY_NAME] = city_details.city.name
                action_result.update_summary({MAXMIND_JSON_CITY: city_details.city.name})

            if (checkattr(city_details, 'subdivisions')):
                subdivision = city_details.subdivisions.most_specific
                if (subdivision is not None) and (len(city_details.subdivisions) > 0):
                    # pylint: disable=E1101
                    curr_data[MAXMIND_JSON_STATE_NAME] = subdivision.name
                    curr_data[MAXMIND_JSON_STATE_ISO_CODE] = subdivision.iso_code
                    action_result.update_summary({MAXMIND_JSON_STATE: subdivision.iso_code})

            if (checkattr(city_details, 'country') and checkattr(city_details.country, 'name')):
                curr_data[MAXMIND_JSON_COUNTRY_NAME] = city_details.country.name
                action_result.update_summary({MAXMIND_JSON_COUNTRY: city_details.country.name})
                if (checkattr(city_details.country, 'iso_code')):
                    # pylint: disable=E1101
                    curr_data[MAXMIND_JSON_COUNTRY_ISO_CODE] = city_details.country.iso_code

            if (checkattr(city_details, 'continent') and checkattr(city_details.continent, 'name')):
                curr_data[MAXMIND_JSON_CONTINENT_NAME] = city_details.continent.name

            if (checkattr(city_details, 'location')):
                # pylint: disable=E1101
                if (checkattr(city_details.location, 'latitude')):
                    curr_data[MAXMIND_JSON_LATITUDE] = city_details.location.latitude
                if (checkattr(city_details.location, 'longitude')):
                    curr_data[MAXMIND_JSON_LONGITUDE] = city_details.location.longitude
                if (checkattr(city_details.location, 'time_zone')):
                    curr_data[MAXMIND_JSON_TIME_ZONE] = city_details.location.time_zone

            if (checkattr(city_details, 'postal') and checkattr(city_details.postal, 'code')):
                # pylint: disable=E1101
                curr_data[MAXMIND_JSON_POSTAL_CODE] = city_details.postal.code

            if (checkattr(city_details, 'traits')):
                # pylint: disable=E1101
                if (checkattr(city_details.traits, 'autonomous_system_number')):
                    curr_data[MAXMIND_JSON_AS_NUMBER] = city_details.traits.autonomous_system_number
                if (checkattr(city_details.traits, 'autonomous_system_organization')):
                    curr_data[MAXMIND_JSON_AS_ORG] = city_details.traits.autonomous_system_organization
                if (checkattr(city_details.traits, 'domain')):
                    curr_data[MAXMIND_JSON_DOMAIN] = city_details.traits.domain

            action_result.set_status(phantom.APP_SUCCESS)

        return phantom.APP_SUCCESS

    def handle_action(self, param):
        """
        """

        if (self.get_action_identifier() == self.ACTION_ID_LOOKUP_IP_GEO_LOCATION):
            self._handle_lookup_ip_list(param)

        return self.get_status()
