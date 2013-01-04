import base64
import urllib
from httplib import HTTPSConnection


VERSION = (0, 1, 1, 'final', 0)

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
        self.host = host or 'app.customer.io'
        self.port = port or 443
        self.url_prefix = url_prefix or '/api/v1'

    def get_customer_query_string(self, customer_id):
        return '%s/customers/%s' % (self.url_prefix, customer_id)

    def get_event_query_string(self, customer_id):
        return '%s/customers/%s/events' % (self.url_prefix, customer_id)

    def send_request(self, method, query_string, data):
        encoded_data = {}
        for key, value in data.items():
            if isinstance(value, unicode):
                encoded_data[key] = value.encode('utf8')
            else:
                encoded_data[key] = value
        data_string = urllib.urlencode(encoded_data)
        http = HTTPSConnection(self.host, self.port)
        basic_auth = base64.encodestring('%s:%s' % (self.site_id, self.api_key)).replace('\n', '')
        headers = {
            'Authorization': 'Basic %s' % basic_auth,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': len(data_string),
        }
        http.request(method, query_string, data_string, headers)
        result_status = http.getresponse().status
        if result_status != 200:
            raise CustomerIOException('%s: %s %s' % (result_status, query_string, data_string))

    def identify(self, **kwargs):
        url = self.get_customer_query_string(kwargs['id'])
        self.send_request('PUT', url, kwargs)

    def track(self, customer_id, name, **data):
        url = self.get_event_query_string(customer_id)
        encoded_data = {
            'name': name,
        }
        for key, value in data.iteritems():
            encoded_data['data[%s]' % key] = value
        self.send_request('POST', url, encoded_data)
