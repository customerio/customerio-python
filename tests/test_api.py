import base64
import json
import unittest
from functools import partial
from importlib.metadata import version

import urllib3

from customerio import (
    APIClient,
    CustomerIOException,
    Regions,
    SendEmailRequest,
    SendInAppRequest,
    SendInboxMessageRequest,
    SendPushRequest,
    SendSMSRequest,
    SendWhatsAppRequest,
)
from tests.server import HTTPSTestCase

ClientVersion = version("customerio")

# test uses a self signed certificate so disable the warning messages
urllib3.disable_warnings()


class TestAPIClient(HTTPSTestCase):
    """Starts server which the client connects to in the following tests"""

    def setUp(self):
        self.client = APIClient(
            key="app_api_key",
            url=f"https://{self.server.server_address[0]}:{self.server.server_port}",
        )

        # do not verify the ssl certificate as it is self signed
        # should only be done for tests
        self.client.http.verify = False

    def _check_request(self, resp, rq, *args, **kwargs):
        request = resp.request
        self.assertEqual(request.method, rq["method"])
        self.assertEqual(json.loads(request.body.decode("utf-8")), rq["body"])
        self.assertEqual(request.headers["Authorization"], rq["authorization"])
        self.assertEqual(request.headers["Content-Type"], rq["content_type"])
        self.assertEqual(int(request.headers["Content-Length"]), len(json.dumps(rq["body"])))
        self.assertTrue(
            request.url.endswith(rq["url_suffix"]),
            "url: {} expected suffix: {}".format(request.url, rq["url_suffix"]),
        )

    def test_client_setup(self):
        client = APIClient(key="app_api_key")
        self.assertEqual(client.url, f"https://{Regions.US.api_host}")

        client = APIClient(key="app_api_key", region=Regions.US)
        self.assertEqual(client.url, f"https://{Regions.US.api_host}")

        client = APIClient(key="app_api_key", region=Regions.EU)
        self.assertEqual(client.url, f"https://{Regions.EU.api_host}")

        self.assertEqual(
            self.client.http.headers["User-Agent"], f"Customer.io Python Client/{ClientVersion}"
        )

        # Raises an exception when an invalid region is passed in
        with self.assertRaises(CustomerIOException):
            APIClient(key="app_api_key", region="au")

    def test_send_email(self):
        data = "1,2,3"
        expected = base64.b64encode(bytes(data, "utf-8")).decode()

        self.client.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "authorization": "Bearer app_api_key",
                    "content_type": "application/json",
                    "url_suffix": "/v1/send/email",
                    "body": {
                        "identifiers": {"id": "customer_1"},
                        "transactional_message_id": 100,
                        "subject": "transactional message",
                        "attachments": {"sample.csv": expected},
                    },
                },
            )
        )

        email = SendEmailRequest(
            identifiers={"id": "customer_1"},
            transactional_message_id=100,
            subject="transactional message",
        )
        email.attach("sample.csv", data)

        self.client.send_email(email)

    def test_send_push(self):
        self.client.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "authorization": "Bearer app_api_key",
                    "content_type": "application/json",
                    "url_suffix": "/v1/send/push",
                    "body": {
                        "identifiers": {"id": "customer_1"},
                        "transactional_message_id": 100,
                        "title": "transactional push message",
                        "message": "push message content",
                    },
                },
            )
        )

        push = SendPushRequest(
            identifiers={"id": "customer_1"},
            transactional_message_id=100,
            title="transactional push message",
            message="push message content",
        )

        self.client.send_push(push)

    def test_send_sms(self):
        self.client.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "authorization": "Bearer app_api_key",
                    "content_type": "application/json",
                    "url_suffix": "/v1/send/sms",
                    "body": {"identifiers": {"id": "customer_1"}, "transactional_message_id": 100},
                },
            )
        )

        sms = SendSMSRequest(
            identifiers={"id": "customer_1"},
            transactional_message_id=100,
        )

        self.client.send_sms(sms)

    def test_send_whatsapp(self):
        self.client.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "authorization": "Bearer app_api_key",
                    "content_type": "application/json",
                    "url_suffix": "/v1/send/whatsapp",
                    "body": {
                        "identifiers": {"id": "customer_1"},
                        "transactional_message_id": 100,
                        "to": "+15551234567",
                        "tracked": True,
                    },
                },
            )
        )

        whatsapp = SendWhatsAppRequest(
            identifiers={"id": "customer_1"},
            transactional_message_id=100,
            to="+15551234567",
            tracked=True,
        )

        self.client.send_whatsapp(whatsapp)

    def test_send_inbox_message(self):
        self.client.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "authorization": "Bearer app_api_key",
                    "content_type": "application/json",
                    "url_suffix": "/v1/send/inbox_message",
                    "body": {"identifiers": {"id": "customer_1"}, "transactional_message_id": 100},
                },
            )
        )

        inbox_message = SendInboxMessageRequest(
            identifiers={"id": "customer_1"},
            transactional_message_id=100,
        )

        self.client.send_inbox_message(inbox_message)

    def test_send_in_app(self):
        self.client.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "authorization": "Bearer app_api_key",
                    "content_type": "application/json",
                    "url_suffix": "/v1/send/in_app",
                    "body": {"identifiers": {"id": "customer_1"}, "transactional_message_id": 100},
                },
            )
        )

        in_app = SendInAppRequest(
            identifiers={"id": "customer_1"},
            transactional_message_id=100,
        )

        self.client.send_in_app(in_app)

    def test_create_import(self):
        import_data = {
            "name": "Device tokens",
            "data_file_url": "https://example.com/devices.csv",
            "type": "device",
            "identifier": "id",
        }

        self.client.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "authorization": "Bearer app_api_key",
                    "content_type": "application/json",
                    "url_suffix": "/v1/imports",
                    "body": {"import": import_data},
                },
            )
        )

        self.client.create_import(import_data)

    def test_create_import_requires_fields(self):
        with self.assertRaises(CustomerIOException):
            self.client.create_import({"name": "Device tokens", "type": "device"})

        with self.assertRaises(CustomerIOException):
            self.client.create_import(
                {"name": "Device tokens", "data_file_url": "https://example.com/devices.csv"}
            )

        with self.assertRaises(CustomerIOException):
            self.client.create_import("https://example.com/devices.csv")

    def test_get_import(self):
        requests_seen = []

        def check_request(resp, *args, **kwargs):
            request = resp.request
            requests_seen.append(request)
            self.assertEqual(request.method, "GET")
            self.assertIsNone(request.body)
            self.assertEqual(request.headers["Authorization"], "Bearer app_api_key")
            self.assertTrue(
                request.url.endswith("/v1/imports/15"),
                f"url: {request.url} expected suffix: /v1/imports/15",
            )

        self.client.http.hooks = dict(response=check_request)

        self.assertEqual(self.client.get_import(15), {})
        self.assertEqual(len(requests_seen), 1)

    def test_get_import_requires_id(self):
        with self.assertRaises(CustomerIOException):
            self.client.get_import(None)

        with self.assertRaises(CustomerIOException):
            self.client.get_import("")


if __name__ == "__main__":
    unittest.main()
