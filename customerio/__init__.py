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

        self.port = port or 443
        self.url_prefix = url_prefix or '/api/v1'

    def get_customer_query_string(self, customer_id):
        return '%s/customers/%s' % (self.url_prefix, customer_id)

    def get_event_query_string(self, customer_id):
        return '%s/customers/%s/events' % (self.url_prefix, customer_id)

    def send_request(self, host, method, query_string, data):
        data = json.dumps(data)
        http = HTTPSConnection(host, self.port)
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

    def identify(self, host="track.customer.io", **kwargs):
        url = self.get_customer_query_string(kwargs['id'])
        self.send_request(host, 'PUT', url, kwargs)

    def track(self, customer_id, name, host="track.customer.io", **data):
        url = self.get_event_query_string(customer_id)
        post_data = {
            'name': name,
            'data': data,
        }
        self.send_request(host, 'POST', url, post_data)

    def delete(self, host="track.customer.io", **kwargs):
        """Delete a customer profile."""

        url = self.get_customer_query_string(kwargs['id'])
        content = self.send_request(host, 'DELETE', url, kwargs)
        # Note -- this method will return a 200 response code
        # even if you try to delete non-existent customer profiles
        # there's never negative feedback from this method.

    def list_customers(self, start_page=1, results=100):
        """Extend the native customer retrieval method

           Customer.io's internal API only allows for 25 results
           at a time. This is a thin wrapper around that to
           conveniently grab more customers
        """
        customers = []
        page = start_page
        results_per_query = 25

        while len(customers) < results:
            next_customer_batch = self._list_customers(page, results_per_query)
            if len(customers) + len(next_customer_batch) <= results:
                customers += next_customer_batch
            else:
                customers += next_customer_batch[:results - len(customers)]
            page += 1
            if len(next_customer_batch) < results_per_query:
                break
        return customers

    def _list_customers(self, page=1, results_per_query=25, host="manage.customer.io"):
        """Get a list of of your customer.io customers.

           This uses Customer.io's internal API for customer retrieval, which
           caps result sets to a maximum of 25 results.
        """

        method = "GET"
        query_string = "/api/v1/customers"
        data = {'page': page, 'per': results_per_query}

        content = self.send_request(host, 'GET', query_string, data)
        content = json.loads(content)
        customers = content.get("customers")
        return customers
    def get_customer_count(self, host="manage.customer.io"):
        """Return the number of customers profiles in your account"""

        method = "GET"
        query_string = "/api/v1/customers"
        content = self.send_request(host, 'GET', query_string, {})
        content = json.loads(content)
        return content.get("total")
