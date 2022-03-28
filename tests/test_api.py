import base64
from datetime import datetime
from functools import partial
import json
import sys
import unittest

from customerio import APIClient, SendEmailRequest, Regions, CustomerIOException
from customerio.__version__ import __version__ as ClientVersion
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
        if (rq['method'] != 'GET'):
            self.assertEqual(json.loads(request.body.decode('utf-8')), rq['body'])
            self.assertEqual(request.headers['Content-Type'], rq['content_type'])
            self.assertEqual(
                int(request.headers['Content-Length']), len(json.dumps(rq['body'])))
        self.assertEqual(request.headers['Authorization'], rq['authorization'])
        self.assertTrue(request.url.endswith(rq['url_suffix']),
                        'url: {} expected suffix: {}'.format(request.url, rq['url_suffix']))

    def test_client_setup(self):
        client = APIClient(key='app_api_key')
        self.assertEqual(client.url, 'https://{host}'.format(host=Regions.US.api_host))

        client = APIClient(key='app_api_key', region=Regions.US)
        self.assertEqual(client.url, 'https://{host}'.format(host=Regions.US.api_host))

        client = APIClient(key='app_api_key', region=Regions.EU)
        self.assertEqual(client.url, 'https://{host}'.format(host=Regions.EU.api_host))

        self.assertEqual(self.client.http.headers['User-Agent'], 'Customer.io Python Client/{}'.format(ClientVersion))

        # Raises an exception when an invalid region is passed in
        with self.assertRaises(CustomerIOException):
            APIClient(key='app_api_key', region='au')

    def test_send_email(self):
        data = "1,2,3"
        expected = base64.b64encode(bytes(data,"utf-8")).decode()

        self.client.http.hooks = dict(response=partial(self._check_request, rq={
            'method': 'POST',
            'authorization': "Bearer app_api_key",
            'content_type': 'application/json',
            'url_suffix': '/v1/send/email',
            'body': {"identifiers": {"id":"customer_1"}, "transactional_message_id": 100, "subject": "transactional message", "attachments":{"sample.csv": expected}},
        }))

        email = SendEmailRequest(
            identifiers={"id":"customer_1"},
            transactional_message_id=100,
            subject="transactional message"
        )
        email.attach('sample.csv', data)

        self.client.send_email(email)

    def test_create_collection(self):
        self.client.http.hooks=dict(response=partial(self._check_request, rq={
            'method': 'POST',
            'authorization': "Bearer app_api_key",
            'content_type': 'application/json',
            'url_suffix': '/collections',
            'body': {"name": "events", "data": [{"eventName": "christmas"}]},
        }))

        data = [
            {
                "eventName": "christmas"
            }
        ]

        self.client.create_collection(name='events', data=data)

        with self.assertRaises(TypeError):
            self.client.create_collection()

    def test_list_collections(self):
        self.client.http.hooks=dict(response=partial(self._check_request, rq={
            'method': 'GET',
            'authorization': "Bearer app_api_key",
            'content_type': 'application/json',
            'url_suffix': '/collections',
        }))

        collections = self.client.list_collections()

    def test_lookup_collection(self):
        self.client.http.hooks=dict(response=partial(self._check_request, rq={
            'method': 'GET',
            'authorization': "Bearer app_api_key",
            'content_type': 'application/json',
            'url_suffix': '/collections/1',
        }))

        collection = self.client.lookup_collection(id=1)

        with self.assertRaises(TypeError):
            self.client.lookup_collection()

    def test_delete_collection(self):
        self.client.http.hooks=dict(response=partial(self._check_request, rq={
            'method': 'DELETE',
            'authorization': "Bearer app_api_key",
            'content_type': 'application/json',
            'url_suffix': '/collections/1',
            'body': {},
        }))

        self.client.delete_collection(id=1)

        with self.assertRaises(TypeError):
            self.client.delete_collection()

    def test_update_collection(self):
        self.client.http.hooks=dict(response=partial(self._check_request, rq={
            'method': 'PUT',
            'authorization': "Bearer app_api_key",
            'content_type': 'application/json',
            'url_suffix': '/collections/1',
            'body': {"name": "events", "data": [{"eventName": "christmas"}]},
        }))

        data = [
            {
                "eventName": "christmas"
            }
        ]

        self.client.update_collection(id=1, name='events', data=data)

        with self.assertRaises(TypeError):
            self.client.update_collection()

    def test_lookup_collection_contents(self):
        self.client.http.hooks=dict(response=partial(self._check_request, rq={
            'method': 'GET',
            'authorization': "Bearer app_api_key",
            'content_type': 'application/json',
            'url_suffix': '/collections/1/content',
        }))

        self.client.lookup_collection_contents(id=1)

        with self.assertRaises(TypeError):
            self.client.lookup_collection_contents()

    def test_update_collection_contents(self):
        self.client.http.hooks=dict(response=partial(self._check_request, rq={
            'method': 'PUT',
            'authorization': "Bearer app_api_key",
            'content_type': 'application/json',
            'url_suffix': '/collections/1/content',
            'body': {"eventName": "christmas"},
        }))

        data = {
            "eventName": "christmas"
        }

        self.client.update_collection_contents(id=1, data=data)

        with self.assertRaises(TypeError):
            self.client.update_collection_contents()

if __name__ == '__main__':
    unittest.main()
