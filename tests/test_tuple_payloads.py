"""Exercise tuple values through real requests JSON preparation, without networking."""

import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from requests import Response
from requests.adapters import BaseAdapter

from customerio import APIClient, CustomerIO, SendEmailRequest


class RecordingAdapter(BaseAdapter):
    def __init__(self):
        self.requests = []

    def send(self, request, **kwargs):
        self.requests.append(request)
        response = Response()
        response.status_code = 200
        response._content = b"{}"
        response.request = request
        return response

    def close(self):
        pass


class TestTuplePayloads(unittest.TestCase):
    def assert_payloads(self, values, expected):
        for operation in ("identify", "track", "batch", "send_email"):
            for pooling in (False, True):
                with self.subTest(operation=operation, pooling=pooling):
                    if operation == "send_email":
                        client = APIClient("test-key", use_connection_pooling=pooling)
                    else:
                        client = CustomerIO("test-site", "test-key", use_connection_pooling=pooling)
                    adapter = RecordingAdapter()
                    original_build_session = client._build_session

                    def build_session(
                        original_build_session=original_build_session, adapter=adapter
                    ):
                        session = original_build_session()
                        session.mount("https://", adapter)
                        return session

                    with patch.object(client, "_build_session", side_effect=build_session), client:
                        if operation == "identify":
                            client.identify("test-person", values=values)
                        elif operation == "track":
                            client.track("test-person", "test-event", data={"values": values})
                        elif operation == "batch":
                            client.batch(
                                [
                                    {
                                        "type": "person",
                                        "action": "identify",
                                        "identifiers": {"id": "test-person"},
                                        "attributes": {"values": values},
                                    }
                                ]
                            )
                        else:
                            client.send_email(
                                SendEmailRequest(
                                    transactional_message_id="test-template",
                                    identifiers={"id": "test-person"},
                                    message_data={"values": values},
                                )
                            )
                    self.assertEqual(len(adapter.requests), 1)
                    payload = json.loads(adapter.requests[0].body)
                    if operation == "track":
                        payload = payload["data"]
                    elif operation == "batch":
                        payload = payload["batch"][0]["attributes"]
                    elif operation == "send_email":
                        payload = payload["message_data"]
                    self.assertEqual(payload["values"], expected)

    def test_datetimes_in_tuples(self):
        values = (datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 2))
        self.assert_payloads(values, [1704067200, 1704153600])
        self.assertIsInstance(values[0], datetime)

    def test_nan_in_tuples(self):
        self.assert_payloads((1, float("nan")), [1, None])

    def test_mixed_nested_containers(self):
        values = ([{"nested": (datetime(2024, 1, 1, tzinfo=timezone.utc), float("nan"))}],)
        self.assert_payloads(values, [[{"nested": [1704067200, None]}]])
        self.assertIsInstance(values[0][0]["nested"], tuple)

    def test_json_native_tuples(self):
        self.assert_payloads((1, "two", False, None, ()), [1, "two", False, None, []])

    def test_existing_list_conversion(self):
        self.assert_payloads(
            [datetime(2024, 1, 1, tzinfo=timezone.utc), float("nan")], [1704067200, None]
        )
