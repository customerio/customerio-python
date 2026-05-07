import threading
import unittest

from customerio.client_base import ClientBase, CustomerIOException


class FakeResponse:
    status_code = 200
    text = "ok"


class FakeSession:
    def __init__(self, request_barrier=None):
        self.closed = False
        self.request_barrier = request_barrier
        self.request_count = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def request(self, *args, **kwargs):
        self.request_count += 1
        if self.request_barrier is not None:
            self.request_barrier.wait(timeout=5)
        return FakeResponse()

    def close(self):
        self.closed = True


class TestClientBase(unittest.TestCase):
    def test_connection_pooling_reuses_session(self):
        client = ClientBase(use_connection_pooling=True)
        sessions = []

        def build_session():
            session = FakeSession()
            sessions.append(session)
            return session

        client._build_session = build_session

        resp1 = client.send_request("POST", "https://example.com", {})
        resp2 = client.send_request("POST", "https://example.com", {})
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp2.status_code, 200)

        self.assertEqual(len(sessions), 1)
        self.assertFalse(sessions[0].closed)

    def test_disabled_connection_pooling_isolates_overlapping_requests(self):
        client = ClientBase(use_connection_pooling=False)
        request_barrier = threading.Barrier(2)
        sessions = []
        responses = []
        errors = []

        def build_session():
            session = FakeSession(request_barrier)
            sessions.append(session)
            return session

        def send_request():
            try:
                responses.append(client.send_request("POST", "https://example.com", {}))
            except Exception as exc:  # pragma: no cover
                errors.append(exc)

        client._build_session = build_session

        threads = [threading.Thread(target=send_request) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(errors, [])
        self.assertEqual(len(responses), 2)
        self.assertTrue(all(r.status_code == 200 for r in responses))
        self.assertEqual(len(sessions), 2)
        self.assertTrue(all(session.closed for session in sessions))
        self.assertTrue(all(session.request_count == 1 for session in sessions))
        self.assertIsNone(client._current_session)

    def test_retry_config_allows_post(self):
        client = ClientBase(retries=5, backoff_factor=0.1)
        session = client._build_session()
        adapter = session.get_adapter("https://example.com")
        retry = adapter.max_retries

        self.assertEqual(retry.total, 5)
        self.assertEqual(retry.backoff_factor, 0.1)
        self.assertIsNone(retry.allowed_methods)
        self.assertEqual(set(retry.status_forcelist), {500, 502, 503, 504})

    def test_non_200_raises_without_retry_wrapper(self):
        client = ClientBase()

        error_response = FakeResponse()
        error_response.status_code = 400
        error_response.text = "bad request"

        def build_session():
            session = FakeSession()
            session.request = lambda *a, **kw: error_response
            return session

        client._build_session = build_session

        with self.assertRaises(CustomerIOException) as ctx:
            client.send_request("POST", "https://example.com", {})

        self.assertIn("400", str(ctx.exception))
        self.assertNotIn("retries", str(ctx.exception))

    def test_2xx_status_codes_accepted(self):
        client = ClientBase()

        for status in [200, 201, 202, 204]:
            response = FakeResponse()
            response.status_code = status
            response.text = "ok"

            def build_session(resp=response):
                session = FakeSession()
                session.request = lambda *a, **kw: resp
                return session

            client._build_session = build_session
            client._current_session = None
            result = client.send_request("POST", "https://example.com", {})
            self.assertEqual(result, "ok")


if __name__ == "__main__":
    unittest.main()
