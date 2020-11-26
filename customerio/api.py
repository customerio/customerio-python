"""
Implements the client that interacts with Customer.io's Transactional API using app keys.
"""
from .client_base import ClientBase

class APIClient(ClientBase):
    def __init__(self, key, url=None, retries=3, timeout=10, backoff_factor=0.02):
        self.url = url or 'https://api.customer.io'
        ClientBase.__init__(self, retries=retries,
                            timeout=timeout, backoff_factor=backoff_factor)
        self.http.headers = {
            "Authorization": "Bearer {key}".format(key=key)}

    def send_email(self, **kwargs):
        return self.send_request('POST', self.url + "/v1/send/email", kwargs)
