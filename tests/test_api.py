from datetime import datetime
from functools import partial
import json
import sys
import unittest

from customerio import APIClient
from tests.server import HTTPSTestCase

import requests
from requests.auth import _basic_auth_str

# test uses a self signed certificate so disable the warning messages
requests.packages.urllib3.disable_warnings()


class TestAPIClient(HTTPSTestCase):
    '''Starts server which the client connects to in the following tests'''

    def setUp(self):
        self.client = APIClient(
            key='app_api_key',
            url="https://{addr}:{port}".format(
                addr=self.server.server_address[0], port=self.server.server_port))

        # do not verify the ssl certificate as it is self signed
        # should only be done for tests
        self.client.http.verify = False

    def _check_request(self, resp, rq, *args, **kwargs):
        request = resp.request
        self.assertEqual(request.method, rq['method'])
        self.assertEqual(json.loads(request.body.decode('utf-8')), rq['body'])
        self.assertEqual(request.headers['Authorization'], rq['authorization'])
        self.assertEqual(request.headers['Content-Type'], rq['content_type'])
        self.assertEqual(
            int(request.headers['Content-Length']), len(json.dumps(rq['body'])))
        self.assertTrue(request.url.endswith(rq['url_suffix']),
                        'url: {} expected suffix: {}'.format(request.url, rq['url_suffix']))

    def test_send_email(self):
        self.client.http.hooks = dict(response=partial(self._check_request, rq={
            'method': 'POST',
            'authorization': "Bearer app_api_key",
            'content_type': 'application/json',
            'url_suffix': '/v1/send/email',
            'body': {"customer_id": "customer_1", "transactional_message_id": 100, "subject": "transactional message"},
        }))

        self.client.send_email(
            "customer_1", transactional_message_id=100, subject="transactional message")

        # with self.assertRaises(TypeError):
        #     self.client.identify(random_attr="some_value")


if __name__ == '__main__':
    unittest.main()
