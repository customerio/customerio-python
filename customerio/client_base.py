"""
Implements the base client that is used by other classes to make requests.
"""

import math
import socket
from datetime import datetime, timezone

from requests import Session
from requests.adapters import DEFAULT_POOLBLOCK, HTTPAdapter
from urllib3.connection import HTTPConnection
from urllib3.util.retry import Retry

from .__version__ import __version__ as ClientVersion

TCP_KEEPALIVE_IDLE_TIMEOUT = 300
TCP_KEEPALIVE_INTERVAL = 60


class CustomerIOException(Exception):
    pass


def _tcp_keepalive_socket_options():
    tcp_protocol = getattr(socket, "SOL_TCP", socket.IPPROTO_TCP)
    tcp_keepidle = getattr(socket, "TCP_KEEPIDLE", getattr(socket, "TCP_KEEPALIVE", None))

    options = list(HTTPConnection.default_socket_options)
    keepalive_options = [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)]
    if tcp_keepidle is not None:
        keepalive_options.append((tcp_protocol, tcp_keepidle, TCP_KEEPALIVE_IDLE_TIMEOUT))
    if hasattr(socket, "TCP_KEEPINTVL"):
        keepalive_options.append((tcp_protocol, socket.TCP_KEEPINTVL, TCP_KEEPALIVE_INTERVAL))

    for option in keepalive_options:
        if option not in options:
            options.append(option)

    return options


class TCPKeepAliveHTTPAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=DEFAULT_POOLBLOCK, **pool_kwargs):
        pool_kwargs.setdefault("socket_options", _tcp_keepalive_socket_options())
        super().init_poolmanager(connections, maxsize, block=block, **pool_kwargs)

    def proxy_manager_for(self, proxy, **proxy_kwargs):
        proxy_kwargs.setdefault("socket_options", _tcp_keepalive_socket_options())
        return super().proxy_manager_for(proxy, **proxy_kwargs)


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
            if result_status != 200:
                raise CustomerIOException(f"{result_status}: {url} {data} {response.text}")
            return response.text

        except Exception as e:
            # Raise exception alerting user that the system might be
            # experiencing an outage and refer them to system status page.
            message = f"""Failed to receive valid response after {self.retries} retries.
Check system status at http://status.customer.io.
Last caught exception -- {type(e)}: {e}
            """
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

        session.mount(
            "https://",
            TCPKeepAliveHTTPAdapter(
                max_retries=Retry(total=self.retries, backoff_factor=self.backoff_factor)
            ),
        )

        return session
