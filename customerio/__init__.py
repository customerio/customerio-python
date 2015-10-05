from __future__ import division
import json
import base64
try:
    from httplib import HTTPSConnection
except ImportError:
    from http.client import HTTPSConnection

from datetime import datetime
try:
    from datetime import timezone
    USE_PY3_TIMESTAMPS = True
except ImportError:
    USE_PY3_TIMESTAMPS = False

import time

VERSION = (0, 1, 9, 'final', 0)


def get_version():
    version = '%s.%s' % (VERSION[0], VERSION[1])
    if VERSION[2]:
        version = '%s.%s' % (version, VERSION[2])
    if VERSION[3:] == ('alpha', 0):
        version = '%s pre-alpha' % version
    else:
        if VERSION[3] != 'final':
            version = '%s %s %s' % (version, VERSION[3], VERSION[4])
    return version


class CustomerIOException(Exception):
    pass


class CustomerIO(object):

    def __init__(self, site_id=None, api_key=None, host=None, port=None, url_prefix=None, json_encoder=json.JSONEncoder):
        self.site_id = site_id
        self.api_key = api_key
        self.host = host or 'track.customer.io'
        self.port = port or 443
        self.url_prefix = url_prefix or '/api/v1'
        self.json_encoder = json_encoder

    def get_customer_query_string(self, customer_id):
        '''Generates a customer API path'''
        return '%s/customers/%s' % (self.url_prefix, customer_id)

    def get_event_query_string(self, customer_id):
        '''Generates an event API path'''
        return '%s/customers/%s/events' % (self.url_prefix, customer_id)

    def send_request(self, method, query_string, data):
        '''Dispatches the request and returns a response'''

        data = json.dumps(self._sanitize(data), cls=self.json_encoder)
        http = HTTPSConnection(self.host, self.port)
        auth = "{site_id}:{api_key}".format(site_id=self.site_id, api_key=self.api_key).encode("utf-8")
        basic_auth = base64.b64encode(auth)

        headers = {
            'Authorization': b" ".join([b"Basic", basic_auth]),
            'Content-Type': 'application/json',
            'Content-Length': len(data),
        }

        http.request(method, query_string, data, headers)
        response = http.getresponse()
        result_status = response.status
        if result_status != 200:
            raise CustomerIOException('%s: %s %s' % (result_status, query_string, data))
        return response.read()

    def identify(self, id, **kwargs):
        '''Identify a single customer by their unique id, and optionally add attributes'''
        url = self.get_customer_query_string(id)
        self.send_request('PUT', url, kwargs)

    def track(self, customer_id, name, **data):
        '''Track an event for a given customer_id'''
        url = self.get_event_query_string(customer_id)
        post_data = {
            'name': name,
            'data': data,
        }
        self.send_request('POST', url, post_data)

    def pageview(self, customer_id, page, **data):
        '''Track a pageview for a given customer_id'''
        url = self.get_event_query_string(customer_id)
        post_data = {
            'type': "page",
            'name': page,
            'data': data,
        }
        self.send_request('POST', url, post_data)

    def backfill(self, customer_id, name, timestamp, **data):
        '''Backfill an event (track with timestamp) for a given customer_id'''
        url = self.get_event_query_string(customer_id)

        if isinstance(timestamp, datetime):
            timestamp = self._datetime_to_timestamp(timestamp)
        elif not isinstance(timestamp, int):
            try:
                timestamp = int(timestamp)
            except Exception as e:
                raise CustomerIOException("{t} is not a valid timestamp ({err})".format(t=timestamp, err=e))

        post_data = {
            'name': name,
            'data': data,
            'timestamp': timestamp
        }

        self.send_request('POST', url, post_data)

    def delete(self, customer_id):
        '''Delete a customer profile'''

        url = self.get_customer_query_string(customer_id)
        self.send_request('DELETE', url, {})

    def _sanitize(self, data):
        for k, v in data.items():
            if isinstance(v, datetime):
                data[k] = self._datetime_to_timestamp(v)
        return data

    def _datetime_to_timestamp(self, dt):
        if USE_PY3_TIMESTAMPS:
            return dt.replace(tzinfo=timezone.utc).timestamp()
        else:
            return int(time.mktime(dt.timetuple()))
