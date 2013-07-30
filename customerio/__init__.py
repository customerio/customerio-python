import os
import json
import base64
import urllib
from httplib import HTTPSConnection

VERSION = (0, 1, 3, 'final', 0)

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
    def __init__(self, site_id=None, api_key=None, host=None, port=None, url_prefix=None):
        self.site_id = site_id
        self.api_key = api_key
        self.host = host or 'track.customer.io'
        self.port = port or 443
        self.url_prefix = url_prefix or '/api/v1'

    def get_customer_query_string(self, customer_id):
        return '%s/customers/%s' % (self.url_prefix, customer_id)

    def get_event_query_string(self, customer_id):
        return '%s/customers/%s/events' % (self.url_prefix, customer_id)

    def send_request(self, method, query_string, data):
        data = json.dumps(data)
        http = HTTPSConnection(self.host, self.port)
        basic_auth = base64.encodestring('%s:%s' % (self.site_id, self.api_key)).replace('\n', '')
        headers = {
            'Authorization': 'Basic %s' % basic_auth,
            'Content-Type': 'application/json',
            'Content-Length': len(data),
        }
        http.request(method, query_string, data, headers)
        result_status = http.getresponse().status
        if result_status != 200:
            raise CustomerIOException('%s: %s %s' % (result_status, query_string, data))

    def identify(self, **kwargs):
        url = self.get_customer_query_string(kwargs['id'])
        self.send_request('PUT', url, kwargs)

    def track(self, customer_id, name, **data):
        url = self.get_event_query_string(customer_id)
        post_data = {
            'name': name,
            'data': data,
        }
        self.send_request('POST', url, post_data)
