import threading
import unittest

from customerio.client_base import ClientBase


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

        self.assertEqual(client.send_request("POST", "https://example.com", {}), "ok")
        self.assertEqual(client.send_request("POST", "https://example.com", {}), "ok")

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
        self.assertEqual(sorted(responses), ["ok", "ok"])
        self.assertEqual(len(sessions), 2)
        self.assertTrue(all(session.closed for session in sessions))
        self.assertTrue(all(session.request_count == 1 for session in sessions))
        self.assertIsNone(client._current_session)


if __name__ == "__main__":
    unittest.main()
