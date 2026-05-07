"""
Implements the base client that is used by other classes to make requests.
"""

import math
from datetime import datetime, timezone

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .__version__ import __version__ as ClientVersion


class CustomerIOException(Exception):
    pass


class ClientBase:
    def __init__(self, retries=3, timeout=10, backoff_factor=0.02, use_connection_pooling=True):
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.use_connection_pooling = use_connection_pooling
        self._current_session = None

    @property
    def http(self):
        if self._current_session is None:
            self._current_session = self._build_session()

        return self._current_session

    def send_request(self, method, url, data):
        """Dispatches the request and returns a response."""

        try:
            if self.use_connection_pooling:
                response = self.http.request(
                    method,
                    url=url,
                    json=self._sanitize(data),
                    timeout=self.timeout,
                )
            else:
                with self._build_session() as http:
                    response = http.request(
                        method,
                        url=url,
                        json=self._sanitize(data),
                        timeout=self.timeout,
                    )

            result_status = response.status_code
            if result_status < 200 or result_status >= 300:
                raise CustomerIOException(f"{result_status}: {url} {data} {response.text}")
            return response.text

        except CustomerIOException:
            raise
        except Exception as e:
            message = (
                f"Failed to receive valid response after {self.retries} retries.\n"
                f"Check system status at http://status.customer.io.\n"
                f"Last caught exception -- {type(e)}: {e}"
            )
            raise CustomerIOException(message) from e

    def _sanitize(self, data):
        return {key: self._sanitize_value(value) for key, value in data.items()}

    def _sanitize_value(self, value):
        if isinstance(value, datetime):
            return self._datetime_to_timestamp(value)
        if isinstance(value, float) and math.isnan(value):
            return None
        return value

    def _datetime_to_timestamp(self, dt):
        return int(dt.replace(tzinfo=timezone.utc).timestamp())

    def _stringify_list(self, customer_ids):
        customer_string_ids = []
        for v in customer_ids:
            if isinstance(v, str):
                customer_string_ids.append(v)
            elif isinstance(v, int):
                customer_string_ids.append(str(v))
            else:
                raise CustomerIOException(f"customer_ids cannot be {type(v)}")
        return customer_string_ids

    def _build_session(self):
        session = Session()
        session.headers["User-Agent"] = f"Customer.io Python Client/{ClientVersion}"

        retry = Retry(
            total=self.retries,
            backoff_factor=self.backoff_factor,
            allowed_methods=None,
            status_forcelist=[500, 502, 503, 504],
            raise_on_status=False,
        )
        session.mount("https://", HTTPAdapter(max_retries=retry))

        return session
