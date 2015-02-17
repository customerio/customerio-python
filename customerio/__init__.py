import json
import base64
from httplib import HTTPSConnection
from datetime import datetime

VERSION = (0, 1, 5, 'final', 0)


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

        data = json.dumps(data, cls=self.json_encoder)
        http = HTTPSConnection(self.host, self.port)
        basic_auth = base64.encodestring('%s:%s' % (self.site_id, self.api_key)).replace('\n', '')
        headers = {
            'Authorization': 'Basic %s' % basic_auth,
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

    def backfill(self, customer_id, name, timestamp, **data):
        '''Backfill an event (track with timestamp) for a given customer_id'''
        url = self.get_event_query_string(customer_id)

        if isinstance(timestamp, datetime):
            timestamp = int((timestamp - datetime(1970, 1, 1)).total_seconds())
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
