# File: maxmind_connector.py
#
# Copyright (c) 2016-2020 Splunk Inc.
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
import os

# Phantom imports
import phantom.app as phantom
from phantom.base_connector import BaseConnector
from phantom.action_result import ActionResult

# THIS Connector imports
from maxmind_consts import *

import geoip2.database
import ipaddress
import sys
import requests
import tarfile
import pathlib
from dateutil import parser
from datetime import datetime

MMDB_DIR = os.path.abspath(os.path.dirname(__file__))
MMDB_FILE_PATH = os.path.join(MMDB_DIR, MMDB_FILE)

# Path to store the tar file downloaded from MaxMind.
MMDB_ZIP_FILE_PATH = os.path.join(MMDB_DIR, MMDB_TAR_FILE)


class MaxmindConnector(BaseConnector):

    # Commands supported by this script
    ACTION_ID_LOOKUP_IP_GEO_LOCATION = "lookup_ip"
    ACTION_ID_TEST_ASSET_CONNECTIVITY = "test_asset_connectivity"
    ACTION_ID_UPDATE_DATABASE = "update_database"
    ACTION_ID_ON_POLL = "on_poll"

    def __init__(self):

        # Call the BaseConnectors init first
        super(MaxmindConnector, self).__init__()

        self.reader = None
        self._ip_address = None
        self._python_version = None
        self._state = {}

    def finalize(self):
        self.save_state(self._state)
        return phantom.APP_SUCCESS

    def initialize(self):
        self._state = self.load_state()

        # Fetching the Python major version
        try:
            self._python_version = int(sys.version_info[0])
        except:
            return self.set_status(phantom.APP_ERROR, "Error occurred while getting the Phantom server's Python major version.")

        # Validate the configuration parameters
        config = self.get_config()
        self._ip_address = config.get('ip_address', MAXMIND_DEFAULT_IP_CONNECTIVITY)
        self._license_key = config.get('license_key')

        try:
            if self._python_version == 2:
                ipaddress.ip_address(unicode(self._ip_address))
            else:
                ipaddress.ip_address(self._ip_address)
        except:
            return self.set_status(phantom.APP_ERROR, "Please provide a valid IP Address in the configuration parameters")

        # Load the country db
        try:
            self.reader = geoip2.database.Reader(MMDB_FILE_PATH)
        except Exception as e:
            self.save_progress(MAXMIND_MSG_DB_LOAD_FAILED, db_file=MMDB_FILE_PATH)
            return self.set_status(phantom.APP_ERROR, MAXMIND_MSG_DB_LOAD_FAILED, e, db_file=MMDB_FILE_PATH)

        self.save_progress(MAXMIND_MSG_DB_LOADED)
        return phantom.APP_SUCCESS

    def _handle_test_connectivity(self, param):

        # Create a ActionResult object to store the result
        self.save_progress('In action handler for: {0}'.format(self.get_action_identifier()))
        self.save_progress('Querying the Maxmind DB for the IP: {}'.format(self._ip_address))

        try:
            _ = self.reader.city(self._ip_address)
        except:
            self.save_progress(MAXMIND_SUCCESS_MSG_IP_NOT_FOUND, ip=self._ip_address)
            self.debug_print(MAXMIND_SUCCESS_MSG_IP_NOT_FOUND.format(ip=self._ip_address))
            self.save_progress("Test Connectivity Passed")
            return self.set_status(phantom.APP_SUCCESS)

        # Found the IP
        self.save_progress(MAXMIND_SUCCESS_MSG_IP_FOUND, ip=self._ip_address)
        self.save_progress("Test Connectivity Passed")
        return self.set_status(phantom.APP_SUCCESS)

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

    def _handle_on_poll(self, param):
        if not self._license_key:
            return self.set_status(phantom.APP_ERROR, 'License key is required to fetch MaxMind database.')

        try:
            if not self._should_download_new_db():
                self.save_progress('The database is already up to date.')
                return self._create_ingested_container()
        except Exception as e:
            err_msg = 'Failed to poll. Reason: {}'.format(e)
            self.debug_print(err_msg)
            return self.set_status(phantom.APP_ERROR, err_msg)

        status = self._handle_update_db(param)
        if phantom.is_fail(status):
            return status

        status = self._create_ingested_container()
        if phantom.is_fail(status):
            return status

        if self.is_poll_now():
            self.save_progress('Successfully updated the database to the latest version')

        return self.set_status(phantom.APP_SUCCESS)

    def _create_ingested_container(self):
        self.debug_print('Creating an ingested container')
        utc_now = datetime.utcnow()
        container = {'name': 'maxmind_ingestion_{0}'.format(utc_now.strftime('%Y-%m-%dT%H:%M:%SZ'))}
        ret_val, message, cid = self.save_container(container)
        self.debug_print(
            'save_container (with artifacts) returns, value: {0}, reason: {1}, id: {2}'.format(ret_val, message, cid))
        return self.set_status(ret_val, message, cid)

    def _should_download_new_db(self):
        """Check if there is a newer MaxMind db to download

        This check will not affect the daily download limit.
        For more info on the daily download, see https://dev.maxmind.com/geoip/updating-databases?lang=en#checking-for-the-latest-release-date
        """
        self.debug_print('Checking if the current database is up to date.')
        db_url = DB_DOWNLOAD_URL.format(self._license_key)

        r = requests.head(db_url)
        if r.status_code != 200:
            raise Exception(
                'Failed to check if the database is up-to-date. Status code: {0}. Error: {1}'.format(r.status_code, r.content))

        headers = r.headers
        last_modified_timestamp = headers['last-modified']
        cached_last_modified_time = self._state.get('db_last_modified_time')

        # if this is the 1st database update
        if not cached_last_modified_time:
            return True

        # Check if the latest db on the server is newer than ours.
        dt = parser.parse(last_modified_timestamp)
        cached_dt = parser.parse(cached_last_modified_time)
        return dt > cached_dt

    def _handle_update_db(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))
        self.debug_print('Updating database.')

        try:
            status, msg = self._download_and_replace_db()
            action_result.set_status(status, msg)
        except Exception as e:
            error_msg = 'Error in downloading or replacing database.'
            action_result.set_status(phantom.APP_ERROR, error_msg, e)

        return action_result.get_status()

    def _download_db(self, save_path, chunk_size=128):
        """Download the latest database from MaxMind."""
        url = DB_DOWNLOAD_URL.format(self._license_key)
        self.debug_print('Downloading database from %s.' % url)

        r = requests.get(url, stream=True)
        if r.status_code != 200:
            raise Exception(
                'Failed to download database. Status Code: {0}. Error: {1}'.format(r.status_code, r.content))

        headers = r.headers
        cached_last_modified_time = headers['last-modified']

        self._state['db_last_modified_time'] = cached_last_modified_time

        with open(save_path, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=chunk_size):
                fd.write(chunk)

    def _replace_db(self, tar_file_path):
        self.debug_print('Replacing old db with the new db.')

        # Extract the ZIP database file and keep only the database part.
        # The ZIP file contains README and other unnecessary files.
        tar = tarfile.open(tar_file_path)
        members = tar.getmembers()
        output_dir = '{0}/'.format(MMDB_DIR)

        for mem in members:
            p = pathlib.Path(mem.name)
            if mem.isfile() and p.parts[1].endswith('mmdb'):
                # Get rid of the wrapping folder here.
                mem.name = p.parts[1]

                # Replace the old db with the new one.
                self.debug_print('Saving the new database at {0}{1}'.format(output_dir, mem.name))
                tar.extract(mem, output_dir)

        self.debug_print('Removing the ZIP database file.')
        os.remove(tar_file_path)

    def _download_and_replace_db(self):
        self.debug_print('Downloading database.')

        self._download_db(MMDB_ZIP_FILE_PATH)
        self._replace_db(MMDB_ZIP_FILE_PATH)

        self.debug_print('Successfully updated database.')
        return phantom.APP_SUCCESS, 'Successfully updated database.'

    def handle_action(self, param):
        """
        """
        action = self.get_action_identifier()

        if (action == self.ACTION_ID_LOOKUP_IP_GEO_LOCATION):
            self._handle_lookup_ip_list(param)
        elif (action == self.ACTION_ID_UPDATE_DATABASE):
            self._handle_update_db(param)
        elif (action == self.ACTION_ID_TEST_ASSET_CONNECTIVITY):
            self._handle_test_connectivity(param)
        elif (action == self.ACTION_ID_ON_POLL):
            self._handle_on_poll(param)

        return self.get_status()


if __name__ == '__main__':

    import json
    # import pudb
    from traceback import format_exc

    # pudb.set_trace()

    if (len(sys.argv) < 2):
        print('No test json specified as input')
        exit(0)

    with open(sys.argv[1]) as f:
        in_json = f.read()
        in_json = json.loads(in_json)
        print(json.dumps(in_json, indent=4))
        connector = MaxmindConnector()
        connector.print_progress_message = True
        try:
            ret_val = connector._handle_action(json.dumps(in_json), None)
        except:
            print(format_exc())
        print(json.dumps(json.loads(ret_val), indent=4))

    exit(0)
