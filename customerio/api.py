"""
Implements the client that interacts with Customer.io's App API using app keys.
"""
import base64
from .client_base import ClientBase, CustomerIOException


class APIClient(ClientBase):
    def __init__(self, key, url=None, retries=3, timeout=10, backoff_factor=0.02):
        self.url = url or 'https://api.customer.io'
        ClientBase.__init__(self, retries=retries,
                            timeout=timeout, backoff_factor=backoff_factor)
        self.http.headers = {
            "Authorization": "Bearer {key}".format(key=key)}

    def send_email(self, request):
        if isinstance(request, SendEmailRequest):
            request = request._to_dict()
        return self.send_request('POST', self.url + "/v1/send/email", request)


class SendEmailRequest(object):
    def __init__(self,
            transactional_message_id=None,
            to=None,
            identifiers=None,
            _from=None,
            from_id=None,
            headers=None,
            reply_to=None,
            reply_to_id=None,
            bcc=None,
            subject=None,
            preheader=None,
            body=None,
            plaintext_body=None,
            amp_body=None,
            fake_bcc=None,
            disable_message_retention=None,
            send_to_unsubscribed=None,
            tracked=None,
            queue_draft=None,
            message_data=None,
            attachments=None,
        ):

        self.transactional_message_id = transactional_message_id
        self.to = to
        self.identifiers = identifiers
        self._from = _from
        self.from_id = from_id
        self.headers = headers
        self.reply_to = reply_to
        self.reply_to_id = reply_to_id
        self.bcc = bcc
        self.subject = subject
        self.preheader = preheader
        self.body = body
        self.plaintext_body = plaintext_body
        self.amp_body = amp_body
        self.fake_bcc = fake_bcc
        self.disable_message_retention = disable_message_retention
        self.send_to_unsubscribed = send_to_unsubscribed
        self.tracked = tracked
        self.queue_draft = queue_draft
        self.message_data = message_data
        self.attachments = attachments

    def add_header(self, name, value):
        if not self.headers:
            self.headers = {}

        if self.headers.get(name, None):
            raise CustomerIOException("header {name} already exists".format(name=name))

        self.headers[name] = value

    def add_attachment(self, name, content, encode=True):
        if not self.attachments:
            self.attachments = {}

        if self.attachments.get(name, None):
            raise CustomerIOException("attachment {name} already exists".format(name=name))

        if encode:
            if isinstance(content, str):
                content = base64.b64encode(content.encode('utf-8')).decode()
            else:
                content = base64.b64encode(content).decode()

        self.attachments[name] = content

    def add_message_data(self, name, value):
        if not self.message_data:
            self.message_data = {}

        if self.message_data.get(name, None):
            raise CustomerIOException("message_data {name} already exists".format(name=name))

        self.message_data[name] = value

    def add_identifier(self, name, value):
        if not self.identifiers:
            self.identifiers = {}

        if self.identifiers.get(name, None):
            raise CustomerIOException("identifier {name} already exists".format(name=name))

        self.identifiers[name] = value

    def _to_dict(self):
        field_map = dict(
            _from="from",
            transactional_message_id="transactional_message_id",
            to="to",
            identifiers="identifiers",
            from_id="from_id",
            headers="headers",
            reply_to="reply_to",
            reply_to_id="reply_to_id",
            bcc="bcc",
            subject="subject",
            preheader="preheader",
            body="body",
            plaintext_body="plaintext_body",
            amp_body="amp_body",
            fake_bcc="fake_bcc",
            disable_message_retention="disable_message_retention",
            send_to_unsubscribed="send_to_unsubscribed",
            tracked="tracked",
            queue_draft="queue_draft",
            message_data="message_data",
            attachments="attachments",
        )

        data = {}
        for field, name in field_map.items():
            value = getattr(self, field, None)
            if value is not None:
                data[name] = value

        return data
