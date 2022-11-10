"""
Implements the base client that is used by other classes to make requests
"""
from __future__ import division
from datetime import datetime, timezone
import logging
import math

from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .__version__ import __version__ as ClientVersion

class CustomerIOException(Exception):
    pass

class ClientBase(object):
    def __init__(self, retries=3, timeout=10, backoff_factor=0.02, use_connection_pooling=True):
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.use_connection_pooling = use_connection_pooling
        self._current_session = None

    @property
    def http(self):
        if self._current_session is None:
            self._current_session = self._get_session()

        return self._current_session

    def send_request(self, method, url, data):
        '''Dispatches the request and returns a response'''

        try:
            response = self.http.request(
                method, url=url, json=self._sanitize(data), timeout=self.timeout)

            result_status = response.status_code
            if result_status != 200:
                raise CustomerIOException('%s: %s %s %s' % (result_status, url, data, response.text))
            return response.text

        except Exception as e:
            # Raise exception alerting user that the system might be
            # experiencing an outage and refer them to system status page.
            message = '''Failed to receive valid response after {count} retries.
Check system status at http://status.customer.io.
Last caught exception -- {klass}: {message}
            '''.format(klass=type(e), message=e, count=self.retries)
            raise CustomerIOException(message)

        finally:
            self._close()

    def _sanitize(self, data):
        for k, v in data.items():
            if isinstance(v, datetime):
                data[k] = self._datetime_to_timestamp(v)
            if isinstance(v, float) and math.isnan(v):
                data[k] = None
        return data

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
                raise CustomerIOException(
                    'customer_ids cannot be {type}'.format(type=type(v)))
        return customer_string_ids

    # gets a session based on whether we want pooling or not.  If no pooling is desired, we create a new session each time.
    def _get_session(self):
        if (self.use_connection_pooling):
            if (self._current_session is None):
                self._current_session = self._build_session()

            # if we're using pooling, return the existing session.
            logging.debug("Using existing session...")
            return self._current_session
        else:
            # if we're not using pooling, build a new session.
            logging.debug("Creating new session...")
            self._current_session = self._build_session()
        return self._current_session

    # builds the session.
    def _build_session(self):
        session = Session()
        session.headers['User-Agent'] = "Customer.io Python Client/{version}".format(version=ClientVersion)

        # Retry request a number of times before raising an exception
        # also define backoff_factor to delay each retry
        session.mount(
            'https://',
            HTTPAdapter(max_retries=Retry(total=self.retries, backoff_factor=self.backoff_factor)))

        return session

    # closes the session if we're not using connection pooling.
    def _close(self):
        # if we're not using pooling; clean up the resources.
        if (not self.use_connection_pooling):
            self._current_session.close()
            self._current_session = None
