import json
import socket
import unittest
from datetime import datetime
from functools import partial

import urllib3
from requests.auth import _basic_auth_str
from urllib3.connection import HTTPConnection

from customerio import CustomerIO, CustomerIOException, Regions
from customerio.client_base import TCP_KEEPALIVE_IDLE_TIMEOUT, TCP_KEEPALIVE_INTERVAL
from customerio.constants import CIOID, EMAIL, ID
from tests.server import HTTPSTestCase

# test uses a self signed certificate so disable the warning messages
urllib3.disable_warnings()


class TestCustomerIOTrackSignatures(unittest.TestCase):
    def setUp(self):
        self.cio = CustomerIO(site_id="siteid", api_key="apikey")

    def test_track_rejects_event_data_keyword_arguments(self):
        with self.assertRaises(TypeError):
            self.cio.track(customer_id="5", name="purchased", price=23.45)

    def test_track_anonymous_rejects_event_data_keyword_arguments(self):
        with self.assertRaises(TypeError):
            self.cio.track_anonymous(
                anonymous_id=None,
                name="invite",
                recipient="alex.person@example.com",
            )


class TestCustomerIO(HTTPSTestCase):
    """Starts server which the client connects to in the following tests"""

    def setUp(self):
        self.cio = CustomerIO(
            site_id="siteid",
            api_key="apikey",
            host=self.server.server_address[0],
            port=self.server.server_port,
            retries=5,
            backoff_factor=0,
        )

        # do not verify the ssl certificate as it is self signed
        # should only be done for tests
        self.cio.http.verify = False

    def _check_request(self, resp, rq, *args, **kwargs):
        request = resp.request
        body = request.body.decode("utf-8") if isinstance(request.body, bytes) else request.body
        if rq.get("method", None):
            self.assertEqual(request.method, rq["method"])
        if rq.get("body", None):
            self.assertEqual(json.loads(body), rq["body"])
        if rq.get("authorization", None):
            self.assertEqual(request.headers["Authorization"], rq["authorization"])
        if rq.get("content_type", None):
            self.assertEqual(request.headers["Content-Type"], rq["content_type"])
        if rq.get("body", None):
            self.assertEqual(int(request.headers["Content-Length"]), len(json.dumps(rq["body"])))
        if rq.get("url_suffix", None):
            self.assertTrue(
                request.url.endswith(rq["url_suffix"]),
                "url: {} expected suffix: {}".format(request.url, rq["url_suffix"]),
            )

    def test_client_setup(self):
        client = CustomerIO(site_id="site_id", api_key="api_key")
        self.assertEqual(client.host, Regions.US.track_host)

        client = CustomerIO(site_id="site_id", api_key="api_key", region=Regions.US)
        self.assertEqual(client.host, Regions.US.track_host)

        client = CustomerIO(site_id="site_id", api_key="api_key", region=Regions.EU)
        self.assertEqual(client.host, Regions.EU.track_host)

        # Raises an exception when an invalid region is passed in
        with self.assertRaises(CustomerIOException):
            CustomerIO(site_id="site_id", api_key="api_key", region="au")

    def test_keepalive_socket_options_are_configured_on_adapter(self):
        default_socket_options = list(HTTPConnection.default_socket_options)
        client = CustomerIO(site_id="site_id", api_key="api_key")
        socket_options = client.http.adapters["https://"].poolmanager.connection_pool_kw[
            "socket_options"
        ]
        tcp_protocol = getattr(socket, "SOL_TCP", socket.IPPROTO_TCP)
        tcp_keepidle = getattr(socket, "TCP_KEEPIDLE", getattr(socket, "TCP_KEEPALIVE", None))

        for option in default_socket_options:
            self.assertIn(option, socket_options)
        self.assertIn((socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1), socket_options)
        if tcp_keepidle is not None:
            self.assertIn((tcp_protocol, tcp_keepidle, TCP_KEEPALIVE_IDLE_TIMEOUT), socket_options)
        if hasattr(socket, "TCP_KEEPINTVL"):
            self.assertIn(
                (tcp_protocol, socket.TCP_KEEPINTVL, TCP_KEEPALIVE_INTERVAL), socket_options
            )
        self.assertEqual(HTTPConnection.default_socket_options, default_socket_options)

    def test_client_connection_handling(self):
        retries = self.cio.retries
        # should not raise exception as i should be less than retries and
        # therefore the last request should return a valid response
        for i in range(retries):
            self.cio.identify(str(i), fail_count=i)

        # should raise expection as we get invalid responses for all retries
        with self.assertRaises(CustomerIOException):
            self.cio.identify(retries, fail_count=retries)

    def test_identify_call(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "PUT",
                    "authorization": _basic_auth_str("siteid", "apikey"),
                    "content_type": "application/json",
                    "url_suffix": "/customers/1",
                    "body": {"name": "john", "email": "john@test.com"},
                },
            )
        )

        self.cio.identify(id=1, name="john", email="john@test.com")

        with self.assertRaises(TypeError):
            self.cio.identify(random_attr="some_value")

    def test_track_call(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "authorization": _basic_auth_str("siteid", "apikey"),
                    "content_type": "application/json",
                    "url_suffix": "/customers/1/events",
                    "body": {"data": {"email": "john@test.com"}, "name": "sign_up"},
                },
            )
        )

        self.cio.track(customer_id=1, name="sign_up", data={"email": "john@test.com"})

        with self.assertRaises(TypeError):
            self.cio.track(random_attr="some_value")

    def test_track_with_id(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "url_suffix": "/customers/1/events",
                    "body": {
                        "name": "purchase",
                        "data": {"type": "socks"},
                        "id": "01HB4HBDKTFWYZCK01DMRSWRFD",
                    },
                },
            )
        )

        self.cio.track(1, "purchase", {"type": "socks"}, id="01HB4HBDKTFWYZCK01DMRSWRFD")

    def test_track_without_id(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "url_suffix": "/customers/1/events",
                    "body": {"name": "purchase", "data": {"type": "socks"}},
                },
            )
        )

        self.cio.track(1, "purchase", {"type": "socks"})

    def test_track_with_timestamp(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "url_suffix": "/customers/1/events",
                    "body": {
                        "name": "purchase",
                        "data": {"type": "socks"},
                        "timestamp": 1561231234,
                    },
                },
            )
        )

        self.cio.track(1, "purchase", {"type": "socks"}, timestamp=1561231234)

    def test_track_with_id_and_timestamp(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "url_suffix": "/customers/1/events",
                    "body": {
                        "name": "purchase",
                        "data": {"type": "socks"},
                        "id": "01HB4HBDKTFWYZCK01DMRSWRFD",
                        "timestamp": 1561231234,
                    },
                },
            )
        )

        self.cio.track(
            1, "purchase", {"type": "socks"}, id="01HB4HBDKTFWYZCK01DMRSWRFD", timestamp=1561231234
        )

    def test_track_with_invalid_timestamp(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "url_suffix": "/customers/1/events",
                    "body": {"name": "purchase", "data": {"type": "socks"}},
                },
            )
        )

        self.cio.track(1, "purchase", {"type": "socks"}, timestamp="not-a-timestamp")

    def test_track_with_no_data(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "url_suffix": "/customers/1/events",
                    "body": {"name": "login", "data": {}},
                },
            )
        )

        self.cio.track(1, "login")

    def test_track_anonymous_call(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "authorization": _basic_auth_str("siteid", "apikey"),
                    "content_type": "application/json",
                    "url_suffix": "/events",
                    "body": {
                        "data": {"email": "john@test.com"},
                        "name": "sign_up",
                        "anonymous_id": 123,
                    },
                },
            )
        )

        self.cio.track_anonymous(anonymous_id=123, name="sign_up", data={"email": "john@test.com"})

    def test_track_anonymous_invite_with_data_dict(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "authorization": _basic_auth_str("siteid", "apikey"),
                    "content_type": "application/json",
                    "url_suffix": "/events",
                    "body": {
                        "data": {
                            "first_name": "alex",
                            "recipient": "alex.person@example.com",
                        },
                        "name": "invite",
                    },
                },
            )
        )

        self.cio.track_anonymous(
            anonymous_id=None,
            name="invite",
            data={"first_name": "alex", "recipient": "alex.person@example.com"},
        )

    def test_track_anonymous_with_id(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "url_suffix": "/events",
                    "body": {
                        "name": "purchase",
                        "data": {},
                        "anonymous_id": "anon-123",
                        "id": "01HB4HBDKTFWYZCK01DMRSWRFD",
                    },
                },
            )
        )

        self.cio.track_anonymous("anon-123", "purchase", id="01HB4HBDKTFWYZCK01DMRSWRFD")

    def test_track_anonymous_with_timestamp(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "url_suffix": "/events",
                    "body": {
                        "name": "purchase",
                        "data": {"type": "socks"},
                        "anonymous_id": "anon-123",
                        "timestamp": 1561231234,
                    },
                },
            )
        )

        self.cio.track_anonymous("anon-123", "purchase", {"type": "socks"}, timestamp=1561231234)

    def test_pageview_call(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "authorization": _basic_auth_str("siteid", "apikey"),
                    "content_type": "application/json",
                    "url_suffix": "/customers/1/events",
                    "body": {
                        "data": {"referer": "category_1"},
                        "type": "page",
                        "name": "product_1",
                    },
                },
            )
        )

        self.cio.pageview(customer_id=1, page="product_1", referer="category_1")

        with self.assertRaises(TypeError):
            self.cio.pageview(random_attr="some_value")

    def test_delete_call(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "DELETE",
                    "authorization": _basic_auth_str("siteid", "apikey"),
                    "content_type": "application/json",
                    "url_suffix": "/customers/1",
                    "body": {},
                },
            )
        )

        self.cio.delete(customer_id=1)

        with self.assertRaises(TypeError):
            self.cio.delete(random_attr="some_value")

    def test_backfill_call(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "authorization": _basic_auth_str("siteid", "apikey"),
                    "content_type": "application/json",
                    "url_suffix": "/customers/1/events",
                    "body": {
                        "timestamp": 1234567890,
                        "data": {"email": "john@test.com"},
                        "name": "signup",
                    },
                },
            )
        )

        self.cio.backfill(customer_id=1, name="signup", timestamp=1234567890, email="john@test.com")

        with self.assertRaises(TypeError):
            self.cio.backfill(random_attr="some_value")

    def test_base_url(self):
        test_cases = [
            # host, port, prefix, result
            (None, None, None, "https://track.customer.io/api/v1"),
            (None, None, "v2", "https://track.customer.io/v2"),
            (None, None, "/v2/", "https://track.customer.io/v2"),
            ("sub.domain.com", 1337, "/v2/", "https://sub.domain.com:1337/v2"),
            ("/sub.domain.com/", 1337, "/v2/", "https://sub.domain.com:1337/v2"),
            ("http://sub.domain.com/", 1337, "/v2/", "https://sub.domain.com:1337/v2"),
        ]

        for host, port, prefix, result in test_cases:
            cio = CustomerIO(host=host, port=port, url_prefix=prefix)
            self.assertEqual(cio.base_url, result)

    def test_device_call(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "PUT",
                    "authorization": _basic_auth_str("siteid", "apikey"),
                    "content_type": "application/json",
                    "url_suffix": "/customers/1/devices",
                    "body": {"device": {"id": "device_1", "platform": "ios"}},
                },
            )
        )

        self.cio.add_device(customer_id=1, device_id="device_1", platform="ios")
        with self.assertRaises(TypeError):
            self.cio.add_device(random_attr="some_value")

    def test_device_call_last_used(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "PUT",
                    "authorization": _basic_auth_str("siteid", "apikey"),
                    "content_type": "application/json",
                    "url_suffix": "/customers/1/devices",
                    "body": {
                        "device": {"id": "device_2", "platform": "android", "last_used": 1234567890}
                    },
                },
            )
        )

        self.cio.add_device(
            customer_id=1, device_id="device_2", platform="android", last_used=1234567890
        )

    def test_device_call_valid_platform(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "PUT",
                    "authorization": _basic_auth_str("siteid", "apikey"),
                    "content_type": "application/json",
                    "url_suffix": "/customers/1/devices",
                    "body": {"device": {"id": "device_3", "platform": "notsupported"}},
                },
            )
        )

        with self.assertRaises(CustomerIOException):
            self.cio.add_device(customer_id=1, device_id="device_3", platform=None)

    def test_device_call_has_customer_id(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "PUT",
                    "authorization": _basic_auth_str("siteid", "apikey"),
                    "content_type": "application/json",
                    "url_suffix": "/customers/1/devices",
                    "body": {"device": {"id": "device_4", "platform": "ios"}},
                },
            )
        )

        with self.assertRaises(CustomerIOException):
            self.cio.add_device(customer_id="", device_id="device_4", platform="ios")

    def test_device_call_has_device_id(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "PUT",
                    "authorization": _basic_auth_str("siteid", "apikey"),
                    "content_type": "application/json",
                    "url_suffix": "/customers/1/devices",
                    "body": {"device": {"id": "device_5", "platform": "ios"}},
                },
            )
        )

        with self.assertRaises(CustomerIOException):
            self.cio.add_device(customer_id=1, device_id="", platform="ios")

    def test_device_delete_call(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "DELETE",
                    "authorization": _basic_auth_str("siteid", "apikey"),
                    "content_type": "application/json",
                    "url_suffix": "/customers/1/devices/device_1",
                    "body": {},
                },
            )
        )

        self.cio.delete_device(customer_id=1, device_id="device_1")
        with self.assertRaises(TypeError):
            self.cio.delete_device(random_attr="some_value")

    def test_suppress_call(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "authorization": _basic_auth_str("siteid", "apikey"),
                    "content_type": "application/json",
                    "url_suffix": "/customers/1/suppress",
                    "body": {},
                },
            )
        )

        self.cio.suppress(customer_id=1)

        with self.assertRaises(CustomerIOException):
            self.cio.suppress(None)

    def test_unsuppress_call(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "authorization": _basic_auth_str("siteid", "apikey"),
                    "content_type": "application/json",
                    "url_suffix": "/customers/1/unsuppress",
                    "body": {},
                },
            )
        )

        self.cio.unsuppress(customer_id=1)

        with self.assertRaises(CustomerIOException):
            self.cio.unsuppress(None)

    def test_sanitize(self):
        from datetime import timezone

        data_in = dict(dt=datetime(2009, 2, 13, 23, 31, 30, 0, timezone.utc))
        data_out = self.cio._sanitize(data_in)
        self.assertEqual(data_out, dict(dt=1234567890))

    def test_ids_are_encoded_in_url(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "url_suffix": "/customers/1/unsuppress",
                },
            )
        )
        self.cio.unsuppress(customer_id=1)

        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "url_suffix": "/customers/1%2F",
                },
            )
        )
        self.cio.identify(id="1/")

        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "url_suffix": "/customers/1%20/events",
                },
            )
        )
        self.cio.track(customer_id="1 ", name="test", data={})

        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "url_suffix": "/customers/1%2F/devices/2%20",
                },
            )
        )
        self.cio.delete_device(customer_id="1/", device_id="2 ")

    def test_merge_customers_call(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "authorization": _basic_auth_str("siteid", "apikey"),
                    "content_type": "application/json",
                    "url_suffix": "/merge_customers",
                    "body": {
                        "primary": {ID: "CIO123"},
                        "secondary": {EMAIL: "person1@company.com"},
                    },
                },
            )
        )
        self.cio.merge_customers(ID, "CIO123", EMAIL, "person1@company.com")

        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "authorization": _basic_auth_str("siteid", "apikey"),
                    "content_type": "application/json",
                    "url_suffix": "/merge_customers",
                    "body": {"primary": {"cio_id": "CIO456"}, "secondary": {"id": "MyCustomId"}},
                },
            )
        )
        self.cio.merge_customers(CIOID, "CIO456", ID, "MyCustomId")

        with self.assertRaises(CustomerIOException):
            self.cio.merge_customers(
                primary_id_type=EMAIL,
                primary_id="coolperson@cio.com",
                secondary_id_type="something",
                secondary_id="C123",
            )

        with self.assertRaises(CustomerIOException):
            self.cio.merge_customers(
                primary_id_type="not_valid",
                primary_id="coolperson@cio.com",
                secondary_id_type="something",
                secondary_id="C123",
            )

        with self.assertRaises(CustomerIOException):
            self.cio.merge_customers(
                primary_id_type=EMAIL,
                primary_id="",
                secondary_id_type="something",
                secondary_id="C123",
            )
        with self.assertRaises(CustomerIOException):
            self.cio.merge_customers(
                primary_id_type=EMAIL,
                primary_id="coolperson@cio.com",
                secondary_id_type="something",
                secondary_id="",
            )

    def test_batch_call(self):
        self.cio.http.hooks = dict(
            response=partial(
                self._check_request,
                rq={
                    "method": "POST",
                    "authorization": _basic_auth_str("siteid", "apikey"),
                    "content_type": "application/json",
                    "url_suffix": "/api/v2/batch",
                    "body": {
                        "batch": [
                            {
                                "type": "person",
                                "action": "identify",
                                "identifiers": {"id": "1"},
                                "attributes": {"name": "Alice"},
                            },
                            {
                                "type": "person",
                                "action": "event",
                                "identifiers": {"id": "1"},
                                "name": "purchase",
                            },
                        ]
                    },
                },
            )
        )

        self.cio.batch(
            [
                {
                    "type": "person",
                    "action": "identify",
                    "identifiers": {"id": "1"},
                    "attributes": {"name": "Alice"},
                },
                {
                    "type": "person",
                    "action": "event",
                    "identifiers": {"id": "1"},
                    "name": "purchase",
                },
            ]
        )

        with self.assertRaises(CustomerIOException):
            self.cio.batch([])

        with self.assertRaises(CustomerIOException):
            self.cio.batch(None)


if __name__ == "__main__":
    unittest.main()
