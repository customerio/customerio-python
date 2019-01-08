from __future__ import division
from datetime import datetime
import math
import time
import warnings

from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

try:
    from datetime import timezone
    USE_PY3_TIMESTAMPS = True
except ImportError:
    USE_PY3_TIMESTAMPS = False


class CustomerIOException(Exception):
    pass


class CustomerIO(object):

    def __init__(self, site_id=None, api_key=None, host=None, port=None, url_prefix=None, json_encoder=None, retries=3, timeout=10, backoff_factor=0.02):
        self.site_id = site_id
        self.api_key = api_key
        self.host = host or 'track.customer.io'
        self.port = port or 443
        self.url_prefix = url_prefix or '/api/v1'
        self.retries = retries
        self.timeout = timeout
        self.backoff_factor = backoff_factor

        if json_encoder is not None:
            warnings.warn("With the switch to using requests library the `json_encoder` param is no longer used.", DeprecationWarning)

        self.setup_base_url()
        self.setup_connection()

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

    def setup_connection(self):
        self.http = Session()
        # Retry request a number of times before raising an exception
        # also define backoff_factor to delay each retry
        self.http.mount('https://', HTTPAdapter(max_retries=Retry(
            total=self.retries, backoff_factor=self.backoff_factor)))
        self.http.auth = (self.site_id, self.api_key)

    def get_customer_query_string(self, customer_id):
        '''Generates a customer API path'''
        return '{base}/customers/{id}'.format(base=self.base_url, id=customer_id)

    def get_event_query_string(self, customer_id):
        '''Generates an event API path'''
        return '{base}/customers/{id}/events'.format(base=self.base_url, id=customer_id)

    def get_device_query_string(self, customer_id):
        '''Generates a device API path'''
        return '{base}/customers/{id}/devices'.format(base=self.base_url, id=customer_id)

    def send_request(self, method, url, data):
        '''Dispatches the request and returns a response'''

        try:
            response = self.http.request(method, url=url, json=self._sanitize(data), timeout=self.timeout)
        except Exception as e:
            # Raise exception alerting user that the system might be
            # experiencing an outage and refer them to system status page.
            message = '''Failed to receive valid reponse after {count} retries.
Check system status at http://status.customer.io.
Last caught exception -- {klass}: {message}
            '''.format(klass=type(e), message=e, count=self.retries)
            raise CustomerIOException(message)

        result_status = response.status_code
        if result_status != 200:
            raise CustomerIOException('%s: %s %s' % (result_status, url, data))
        return response.text

    def identify(self, id, **kwargs):
        '''Identify a single customer by their unique id, and optionally add attributes'''
        url = self.get_customer_query_string(id)
        self.send_request('PUT', url, kwargs)

    def track(self, customer_id, name, **data):
        '''Track an event for a given customer_id'''
        url = self.get_event_query_string(customer_id)
        post_data = {
            'name': name,
            'data': data,
        }
        self.send_request('POST', url, post_data)

    def pageview(self, customer_id, page, **data):
        '''Track a pageview for a given customer_id'''
        url = self.get_event_query_string(customer_id)
        post_data = {
            'type': "page",
            'name': page,
            'data': data,
        }
        self.send_request('POST', url, post_data)

    def backfill(self, customer_id, name, timestamp, **data):
        '''Backfill an event (track with timestamp) for a given customer_id'''
        url = self.get_event_query_string(customer_id)

        if isinstance(timestamp, datetime):
            timestamp = self._datetime_to_timestamp(timestamp)
        elif not isinstance(timestamp, int):
            try:
                timestamp = int(timestamp)
            except Exception as e:
                raise CustomerIOException("{t} is not a valid timestamp ({err})".format(t=timestamp, err=e))

        post_data = {
            'name': name,
            'data': data,
            'timestamp': timestamp
        }

        self.send_request('POST', url, post_data)

    def delete(self, customer_id):
        '''Delete a customer profile'''
        url = self.get_customer_query_string(customer_id)
        self.send_request('DELETE', url, {})

    def add_device(self, customer_id, device_id, platform, **data):
        '''Add a device to a customer profile'''
        if not customer_id:
            raise CustomerIOException("customer_id cannot be blank in add_device")
        
        if not device_id:
            raise CustomerIOException("device_id cannot be blank in add_device")
        
        if not platform:
            raise CustomerIOException("platform cannot be blank in add_device")

        data.update({
            'id': device_id,
            'platform': platform,
        })
        payload = {'device': data }
        url = self.get_device_query_string(customer_id)
        self.send_request('PUT', url, payload)

    def delete_device(self, customer_id, device_id):
        '''Delete a device from a customer profile'''
        url = self.get_device_query_string(customer_id)
        delete_url = '{base}/{token}'.format(base=url, token=device_id)
        self.send_request('DELETE', delete_url, {})

    def suppress(self, customer_id):
        if not customer_id:
            raise CustomerIOException("customer_id cannot be blank in suppress")

        self.send_request('POST', '{base}/customers/{id}/suppress'.format(base=self.base_url, id=customer_id), {})
    
    def unsuppress(self, customer_id):
        if not customer_id:
            raise CustomerIOException("customer_id cannot be blank in unsuppress")

        self.send_request('POST', '{base}/customers/{id}/unsuppress'.format(base=self.base_url, id=customer_id), {})

    def add_to_segment(self, segment_id, customer_ids):
        '''Add customers to a manual segment, customer_ids should be a list of strings'''
        if not segment_id:
            raise CustomerIOException("segment_id cannot be blank in add_to_segment")

        if not customer_ids:
            raise CustomerIOException("customer_ids cannot be blank in add_to_segment")
        
        if not isinstance(customer_ids, list):
            raise CustomerIOException("customer_ids must be a list in add_to_segment")

        url = '{base}/segments/{id}/add_customers'.format(base=self.base_url, id=segment_id)
        payload = {'ids': self._stringify_list(customer_ids)}
        self.send_request('POST', url, payload)

    def remove_from_segment(self, segment_id, customer_ids):
        '''Remove customers from a manual segment, customer_ids should be a list of strings'''
        if not segment_id:
            raise CustomerIOException("segment_id cannot be blank in remove_from_segment")

        if not customer_ids:
            raise CustomerIOException("customer_ids cannot be blank in remove_from_segment")

        if not isinstance(customer_ids, list):
            raise CustomerIOException("customer_ids must be a list in remove_from_segment")

        url = '{base}/segments/{id}/remove_customers'.format(base=self.base_url, id=segment_id)
        payload = {'ids': self._stringify_list(customer_ids)}
        self.send_request('POST', url, payload)

    def _sanitize(self, data):
        for k, v in data.items():
            if isinstance(v, datetime):
                data[k] = self._datetime_to_timestamp(v)
            if isinstance(v, float) and math.isnan(v):
                data[k] = None
        return data

    def _datetime_to_timestamp(self, dt):
        if USE_PY3_TIMESTAMPS:
            return int(dt.replace(tzinfo=timezone.utc).timestamp())
        else:
            return int(time.mktime(dt.timetuple()))

    def _stringify_list(self, customer_ids):
        customer_string_ids = []
        for v in customer_ids:
            if isinstance(v, str):
                customer_string_ids.append(v)
            elif isinstance(v, int):
                customer_string_ids.append(str(v))
            else:
                raise CustomerIOException('customer_ids cannot be {type}'.format(type=type(v)))
        return customer_string_ids