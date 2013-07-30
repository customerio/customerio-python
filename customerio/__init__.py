import requests, json

VERSION = (0, 1, 3, 'beta', 0)

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
    
        # for instance, 'POST' -> requests.post
        # doing this to maintain the interface
        request_func = getattr(requests, method.lower()) 

        payload = json.dumps(data)

        if self.port == 443:
            full_url = "https://%s/%s" % (self.host, query_string)
        else:
            full_url = "https://%s/%s:%i" % (self.host, query_string, self.port)

        headers = {
            'Content-Type': 'application/json',
        }

        response = request_func(full_url, auth=(self.site_id, self.api_key),
            headers=headers, data=payload)
        if response.status_code != 200:
            raise CustomerIOException('%s: %s %s' % (
                response.status_code,
                query_string,
                payload
            ))

    def identify(self, **kwargs):
        query_string = self.get_customer_query_string(kwargs['id'])
        self.send_request('PUT', query_string, kwargs)

    def track(self, customer_id, name, **data):
        query_string = self.get_event_query_string(customer_id)
        post_data = {
            'name': name, 'data': data,
        }
        self.send_request('POST', query_string, post_data)
