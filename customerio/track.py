"""
Implements the client that interacts with Customer.io's Track API using Site ID and API Keys.
"""
from .client_base import ClientBase, CustomerIOException
from datetime import datetime
import warnings
from urllib.parse import quote

class CustomerIO(ClientBase):
    def __init__(self, site_id=None, api_key=None, host=None, port=None, url_prefix=None, json_encoder=None, retries=3, timeout=10, backoff_factor=0.02):
        self.host = host or 'track.customer.io'
        self.port = port or 443
        self.url_prefix = url_prefix or '/api/v1'

        if json_encoder is not None:
            warnings.warn(
                "With the switch to using requests library the `json_encoder` param is no longer used.", DeprecationWarning)

        self.setup_base_url()
        ClientBase.__init__(self, retries=retries,
                            timeout=timeout, backoff_factor=backoff_factor)
        self.http.auth = (site_id, api_key)

    def _url_encode(self, id):
        return quote(str(id), safe='')

    def setup_base_url(self):
        template = 'https://{host}:{port}/{prefix}'
        if self.port == 443:
            template = 'https://{host}/{prefix}'

        if '://' in self.host:
            self.host = self.host.split('://')[1]

        self.base_url = template.format(
            host=self.host.strip('/'),
            port=self.port,
            prefix=self.url_prefix.strip('/'))

    def get_customer_query_string(self, customer_id):
        '''Generates a customer API path'''
        return '{base}/customers/{id}'.format(base=self.base_url, id=self._url_encode(customer_id))

    def get_event_query_string(self, customer_id):
        '''Generates an event API path'''
        return '{base}/customers/{id}/events'.format(base=self.base_url, id=self._url_encode(customer_id))

    def get_device_query_string(self, customer_id):
        '''Generates a device API path'''
        return '{base}/customers/{id}/devices'.format(base=self.base_url, id=self._url_encode(customer_id))

    def identify(self, id, **kwargs):
        '''Identify a single customer by their unique id, and optionally add attributes'''
        if not id:
            raise CustomerIOException("id cannot be blank in identify")
        url = self.get_customer_query_string(id)
        self.send_request('PUT', url, kwargs)

    def track(self, customer_id, name, **data):
        '''Track an event for a given customer_id'''
        if not customer_id:
            raise CustomerIOException("customer_id cannot be blank in track")
        url = self.get_event_query_string(customer_id)
        post_data = {
            'name': name,
            'data': self._sanitize(data),
        }
        self.send_request('POST', url, post_data)

    def pageview(self, customer_id, page, **data):
        '''Track a pageview for a given customer_id'''
        if not customer_id:
            raise CustomerIOException("customer_id cannot be blank in pageview")
        url = self.get_event_query_string(customer_id)
        post_data = {
            'type': "page",
            'name': page,
            'data': self._sanitize(data),
        }
        self.send_request('POST', url, post_data)

    def backfill(self, customer_id, name, timestamp, **data):
        '''Backfill an event (track with timestamp) for a given customer_id'''
        if not customer_id:
            raise CustomerIOException("customer_id cannot be blank in backfill")

        url = self.get_event_query_string(customer_id)

        if isinstance(timestamp, datetime):
            timestamp = self._datetime_to_timestamp(timestamp)
        elif not isinstance(timestamp, int):
            try:
                timestamp = int(timestamp)
            except Exception as e:
                raise CustomerIOException(
                    "{t} is not a valid timestamp ({err})".format(t=timestamp, err=e))

        post_data = {
            'name': name,
            'data': self._sanitize(data),
            'timestamp': timestamp
        }

        self.send_request('POST', url, post_data)

    def delete(self, customer_id):
        '''Delete a customer profile'''
        if not customer_id:
            raise CustomerIOException("customer_id cannot be blank in delete")

        url = self.get_customer_query_string(customer_id)
        self.send_request('DELETE', url, {})

    def add_device(self, customer_id, device_id, platform, **data):
        '''Add a device to a customer profile'''
        if not customer_id:
            raise CustomerIOException(
                "customer_id cannot be blank in add_device")

        if not device_id:
            raise CustomerIOException(
                "device_id cannot be blank in add_device")

        if not platform:
            raise CustomerIOException("platform cannot be blank in add_device")

        data.update({
            'id': device_id,
            'platform': platform,
        })
        payload = {'device': data}
        url = self.get_device_query_string(customer_id)
        self.send_request('PUT', url, payload)

    def delete_device(self, customer_id, device_id):
        '''Delete a device from a customer profile'''
        if not customer_id:
            raise CustomerIOException("customer_id cannot be blank in delete_device")

        if not device_id:
            raise CustomerIOException("device_id cannot be blank in delete_device")

        url = self.get_device_query_string(customer_id)
        delete_url = '{base}/{token}'.format(base=url, token=self._url_encode(device_id))
        self.send_request('DELETE', delete_url, {})

    def suppress(self, customer_id):
        if not customer_id:
            raise CustomerIOException(
                "customer_id cannot be blank in suppress")

        self.send_request(
            'POST', '{base}/customers/{id}/suppress'.format(base=self.base_url, id=self._url_encode(customer_id)), {})

    def unsuppress(self, customer_id):
        if not customer_id:
            raise CustomerIOException(
                "customer_id cannot be blank in unsuppress")

        self.send_request(
            'POST', '{base}/customers/{id}/unsuppress'.format(base=self.base_url, id=self._url_encode(customer_id)), {})
