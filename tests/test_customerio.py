from datetime import datetime
from functools import partial
import json
import sys
import unittest

from customerio import CustomerIO, CustomerIOException
from tests.server import HTTPSTestCase

import requests
from requests.auth import _basic_auth_str

# test uses a self signed certificate so disable the warning messages
requests.packages.urllib3.disable_warnings()

class TestCustomerIO(HTTPSTestCase):
    '''Starts server which the client connects to in the following tests'''
    def setUp(self):
        self.cio = CustomerIO(
            site_id='siteid',
            api_key='apikey',
            host=self.server.server_address[0],
            port=self.server.server_port,
            retries=5,
            backoff_factor=0)

        # do not verify the ssl certificate as it is self signed
        # should only be done for tests
        self.cio.http.verify = False

    def _check_request(self, resp, rq, *args, **kwargs):
        request = resp.request
        self.assertEqual(request.method, rq['method'])
        self.assertEqual(json.loads(request.body.decode('utf-8')), rq['body'])
        self.assertEqual(request.headers['Authorization'], rq['authorization'])
        self.assertEqual(request.headers['Content-Type'], rq['content_type'])
        self.assertEqual(int(request.headers['Content-Length']), len(json.dumps(rq['body'])))
        self.assertTrue(request.url.endswith(rq['url_suffix']),
            'url: {} expected suffix: {}'.format(request.url, rq['url_suffix']))


    def test_client_connection_handling(self):
        retries = self.cio.retries
        # should not raise exception as i should be less than retries and 
        # therefore the last request should return a valid response
        for i in range(retries):
            self.cio.identify(i, fail_count=i)

        # should raise expection as we get invalid responses for all retries
        with self.assertRaises(CustomerIOException):
            self.cio.identify(retries, fail_count=retries)


    def test_identify_call(self):
        self.cio.http.hooks=dict(response=partial(self._check_request, rq={
            'method': 'PUT',
            'authorization': _basic_auth_str('siteid', 'apikey'),
            'content_type': 'application/json',
            'url_suffix': '/customers/1',
            'body': {"name": "john", "email": "john@test.com"},
        }))

        self.cio.identify(id=1, name='john', email='john@test.com')

        with self.assertRaises(TypeError):
            self.cio.identify(random_attr="some_value")


    def test_track_call(self):
        self.cio.http.hooks=dict(response=partial(self._check_request, rq={
            'method': 'POST',
            'authorization': _basic_auth_str('siteid', 'apikey'),
            'content_type': 'application/json',
            'url_suffix': '/customers/1/events',
            'body': {"data": {"email": "john@test.com"}, "name": "sign_up"},
        }))

        self.cio.track(customer_id=1, name='sign_up', email='john@test.com')

        with self.assertRaises(TypeError):
            self.cio.track(random_attr="some_value")


    def test_pageview_call(self):
        self.cio.http.hooks=dict(response=partial(self._check_request, rq={
            'method': 'POST',
            'authorization': _basic_auth_str('siteid', 'apikey'),
            'content_type': 'application/json',
            'url_suffix': '/customers/1/events',
            'body': {"data": {"referer": "category_1"}, "type": "page", "name": "product_1"},
        }))

        self.cio.pageview(customer_id=1, page='product_1', referer='category_1')

        with self.assertRaises(TypeError):
            self.cio.pageview(random_attr="some_value")


    def test_delete_call(self):
        self.cio.http.hooks=dict(response=partial(self._check_request, rq={
            'method': 'DELETE',
            'authorization': _basic_auth_str('siteid', 'apikey'),
            'content_type': 'application/json',
            'url_suffix': '/customers/1',
            'body': {},
        }))

        self.cio.delete(customer_id=1)

        with self.assertRaises(TypeError):
            self.cio.delete(random_attr="some_value")


    def test_backfill_call(self):
        self.cio.http.hooks=dict(response=partial(self._check_request, rq={
            'method': 'POST',
            'authorization': _basic_auth_str('siteid', 'apikey'),
            'content_type': 'application/json',
            'url_suffix': '/customers/1/events',
            'body': {"timestamp": 1234567890, "data": {"email": "john@test.com"}, "name": "signup"},
        }))

        self.cio.backfill(customer_id=1, name='signup', timestamp=1234567890, email='john@test.com')

        with self.assertRaises(TypeError):
            self.cio.backfill(random_attr="some_value")


    def test_base_url(self):
        test_cases = [
            # host, port, prefix, result
            (None, None, None, 'https://track.customer.io/api/v1'),
            (None, None, 'v2', 'https://track.customer.io/v2'),
            (None, None, '/v2/', 'https://track.customer.io/v2'),
            ('sub.domain.com', 1337, '/v2/', 'https://sub.domain.com:1337/v2'),
            ('/sub.domain.com/', 1337, '/v2/', 'https://sub.domain.com:1337/v2'),
            ('http://sub.domain.com/', 1337, '/v2/', 'https://sub.domain.com:1337/v2'),
        ]

        for host, port, prefix, result in test_cases:
            cio = CustomerIO(host=host, port=port, url_prefix=prefix)
            self.assertEqual(cio.base_url, result)


    @unittest.skipIf(sys.version_info.major > 2, "python2 specific test case")
    def test_sanitize_py2(self):
        data_in = dict(dt=datetime.fromtimestamp(1234567890))
        data_out = self.cio._sanitize(data_in)
        self.assertEqual(data_out, dict(dt=1234567890))


    @unittest.skipIf(sys.version_info.major < 3, "python3 specific test case")
    def test_sanitize_py3(self):
        from datetime import timezone
        data_in = dict(dt=datetime(2009, 2, 13, 23, 31, 30, 0, timezone.utc))
        data_out = self.cio._sanitize(data_in)
        self.assertEqual(data_out, dict(dt=1234567890))


if __name__ == '__main__':
    unittest.main()
