import json
import unittest
from functools import partial

import urllib3

from customerio import (
    Client,
    CustomerIOException,
    KeyCapabilityError,
    Regions,
    SendEmailRequest,
    SendInAppRequest,
    SendInboxMessageRequest,
    SendPushRequest,
    SendSMSRequest,
    SendWhatsAppRequest,
)
from tests.server import HTTPSTestCase

# test uses a self signed certificate so disable the warning messages
urllib3.disable_warnings()

US_KEY = "ak_us_0123456789ABCDEFGHIJKLMNOPQRSTUV_000000"
EU_KEY = "ak_eu_0123456789ABCDEFGHIJKLMNOPQRSTUV_000000"
PUBLIC_KEY = "wk_us_0123456789ABCDEFGHIJKLMNOPQRSTUV_000000"
LEGACY_KEY = "abc123"

EMAIL = {"to": "a@example.com", "identifiers": {"id": "user_123"}, "transactional_message_id": 5}


class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self.text = json.dumps(body)

    def json(self):
        return json.loads(self.text)


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.request_count = 0

    def request(self, *args, **kwargs):
        self.request_count += 1
        return self.response

    def close(self):
        pass


class TestClientSetup(unittest.TestCase):
    def test_requires_api_key(self):
        with self.assertRaises(CustomerIOException):
            Client(api_key="")

    def test_rejects_invalid_region(self):
        with self.assertRaises(CustomerIOException):
            Client(api_key=US_KEY, region="eu")

    def test_region_comes_from_the_key(self):
        self.assertEqual(Client(api_key=US_KEY).region, Regions.US)
        self.assertEqual(Client(api_key=EU_KEY).region, Regions.EU)
        self.assertEqual(Client(api_key=PUBLIC_KEY).region, Regions.US)

        cio = Client(api_key=EU_KEY)
        self.assertEqual(cio.track_client.base_url, f"https://{Regions.EU.track_host}/api/v1")
        self.assertEqual(cio.api_client.url, f"https://{Regions.EU.api_host}")

    def test_explicit_region_wins_over_the_key(self):
        cio = Client(api_key=EU_KEY, region=Regions.US)
        self.assertEqual(cio.region, Regions.US)
        self.assertEqual(cio.track_client.base_url, f"https://{Regions.US.track_host}/api/v1")
        self.assertEqual(cio.api_client.url, f"https://{Regions.US.api_host}")

    def test_legacy_keys_keep_the_region_option_and_us_default(self):
        self.assertEqual(Client(api_key=LEGACY_KEY).region, Regions.US)
        self.assertEqual(Client(api_key=LEGACY_KEY, region=Regions.EU).region, Regions.EU)

    def test_both_clients_use_bearer_auth(self):
        cio = Client(api_key=US_KEY)
        self.assertIsNone(cio.track_client.http.auth)
        self.assertEqual(cio.track_client.http.headers["Authorization"], f"Bearer {US_KEY}")
        self.assertEqual(cio.api_client.http.headers["Authorization"], f"Bearer {US_KEY}")


class TestClientRequests(HTTPSTestCase):
    """Starts server which the client connects to in the following tests"""

    def setUp(self):
        url = f"https://{self.server.server_address[0]}:{self.server.server_port}"
        self.cio = self._client(US_KEY, url)

    def _client(self, key, url):
        cio = Client(api_key=key, track_url=url, api_url=url, retries=5, backoff_factor=0)

        # do not verify the ssl certificate as it is self signed
        # should only be done for tests
        cio.track_client.http.verify = False
        cio._api_client.http.verify = False
        return cio

    def _check_request(self, resp, rq, *args, **kwargs):
        request = resp.request
        self.assertEqual(request.method, rq["method"])
        self.assertEqual(request.headers["Authorization"], rq["authorization"])
        self.assertTrue(
            request.url.endswith(rq["url_suffix"]),
            "url: {} expected suffix: {}".format(request.url, rq["url_suffix"]),
        )

    def _expect(self, http, method, url_suffix, key=US_KEY):
        http.hooks = dict(
            response=partial(
                self._check_request,
                rq={"method": method, "authorization": f"Bearer {key}", "url_suffix": url_suffix},
            )
        )

    def test_tracking_goes_to_the_track_api_with_bearer(self):
        http = self.cio.track_client.http

        self._expect(http, "PUT", "/api/v1/customers/user_123")
        self.cio.identify("user_123", email="a@example.com")

        self._expect(http, "POST", "/api/v1/customers/user_123/events")
        self.cio.track("user_123", "order_completed", data={"price": 1})

        self._expect(http, "POST", "/api/v1/events")
        self.cio.track_anonymous("anon_1", "viewed")

        self._expect(http, "POST", "/api/v1/customers/user_123/events")
        self.cio.pageview("user_123", "/pricing")

    def test_send_methods_go_to_the_app_api_with_bearer(self):
        http = self.cio.api_client.http
        identifiers = {"id": "user_123"}
        sends = [
            (self.cio.send_email, SendEmailRequest(**EMAIL), "email"),
            (self.cio.send_push, SendPushRequest(identifiers=identifiers), "push"),
            (self.cio.send_sms, SendSMSRequest(identifiers=identifiers), "sms"),
            (self.cio.send_whatsapp, SendWhatsAppRequest(identifiers=identifiers), "whatsapp"),
            (
                self.cio.send_inbox_message,
                SendInboxMessageRequest(identifiers=identifiers),
                "inbox_message",
            ),
            (self.cio.send_in_app, SendInAppRequest(identifiers=identifiers), "in_app"),
        ]

        for send, request, path in sends:
            self._expect(http, "POST", f"/v1/send/{path}")
            self.assertEqual(send(request), {})

        self._expect(http, "POST", "/v1/send/email")
        self.cio.send_email(dict(EMAIL))

    def test_public_key_can_still_track(self):
        url = f"https://{self.server.server_address[0]}:{self.server.server_port}"
        cio = self._client(PUBLIC_KEY, url)

        self._expect(cio.track_client.http, "POST", "/api/v1/customers/user_123/events", PUBLIC_KEY)
        cio.track("user_123", "viewed")


class TestClientKeyCapability(unittest.TestCase):
    def _fail_with(self, client, status, body):
        session = FakeSession(FakeResponse(status, body))
        client._build_session = lambda: session
        client._current_session = None
        return session

    def test_public_key_raises_on_transactional_calls_without_a_request(self):
        cio = Client(api_key=PUBLIC_KEY)
        session = self._fail_with(cio._api_client, 200, {})

        for send in [
            cio.send_email,
            cio.send_push,
            cio.send_sms,
            cio.send_whatsapp,
            cio.send_inbox_message,
            cio.send_in_app,
        ]:
            with self.assertRaises(KeyCapabilityError) as ctx:
                send(dict(EMAIL))
            self.assertEqual(ctx.exception.capability, "transactional")
            self.assertIsNone(ctx.exception.status_code)
            self.assertIn("public keys (wk_) are for tracking only", str(ctx.exception))

        with self.assertRaises(KeyCapabilityError):
            cio.api_client  # noqa: B018

        self.assertEqual(session.request_count, 0)

    def test_401_from_the_app_api_becomes_key_capability_error(self):
        cio = Client(api_key=US_KEY)
        self._fail_with(cio._api_client, 401, {"meta": {"error": "unauthorized"}})

        with self.assertRaises(KeyCapabilityError) as ctx:
            cio.send_email(dict(EMAIL))

        self.assertEqual(ctx.exception.capability, "transactional")
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(
            str(ctx.exception), "This key can't send transactional messages (401): unauthorized"
        )
        self.assertIsInstance(ctx.exception.__cause__, CustomerIOException)
        self.assertNotIsInstance(ctx.exception.__cause__, KeyCapabilityError)

    def test_403_from_the_track_api_becomes_key_capability_error(self):
        cio = Client(api_key=US_KEY)
        self._fail_with(cio.track_client, 403, {"meta": {"error": "forbidden"}})

        with self.assertRaises(KeyCapabilityError) as ctx:
            cio.identify("1")

        self.assertEqual(ctx.exception.capability, "track")
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(str(ctx.exception), "This key can't send tracking data (403): forbidden")
        self.assertIsInstance(ctx.exception.__cause__, CustomerIOException)

    def test_other_request_errors_pass_through_unchanged(self):
        cio = Client(api_key=US_KEY)
        self._fail_with(cio.track_client, 400, {"meta": {"error": "bad request"}})

        with self.assertRaises(CustomerIOException) as ctx:
            cio.identify("1")

        self.assertNotIsInstance(ctx.exception, KeyCapabilityError)
        self.assertIn("400", str(ctx.exception))

    def test_missing_params_still_raise_before_a_request(self):
        cio = Client(api_key=US_KEY)
        session = self._fail_with(cio.track_client, 200, {})

        with self.assertRaises(CustomerIOException) as ctx:
            cio.identify("")

        self.assertNotIsInstance(ctx.exception, KeyCapabilityError)
        self.assertEqual(session.request_count, 0)


if __name__ == "__main__":
    unittest.main()
