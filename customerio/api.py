"""
Implements the client that interacts with Customer.io's App API using app keys.
"""
import base64
import json
from .client_base import ClientBase, CustomerIOException
from .regions import Regions, Region


class APIClient(ClientBase):
    def __init__(self, key, url=None, region=Regions.US, retries=3, timeout=10, backoff_factor=0.02):
        if not isinstance(region, Region):
            raise CustomerIOException('invalid region provided')

        self.url = url or 'https://{host}'.format(host=region.api_host)
        ClientBase.__init__(self, retries=retries,
                            timeout=timeout, backoff_factor=backoff_factor)
        self.http.headers = {
            "Authorization": "Bearer {key}".format(key=key)}

    def send_email(self, request):
        if isinstance(request, SendEmailRequest):
            request = request._to_dict()
        resp = self.send_request('POST', self.url + "/v1/send/email", request)
        return json.loads(resp)



class SendEmailRequest(object):
    '''An object with all the options avaiable for triggering a transactional message'''
    def __init__(self,
            transactional_message_id=None,
            to=None,
            identifiers=None,
            _from=None,
            headers=None,
            reply_to=None,
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
        self.headers = headers
        self.reply_to = reply_to
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

    def attach(self, name, content, encode=True):
        '''Helper method to add base64 encode the attachments'''
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

    def _to_dict(self):
        '''Build a request payload fromt the object'''
        field_map = dict(
            # from is reservered keyword hence the object has the field
            # `_from` but in the request payload we map it to `from`
            _from="from",
            # field name is the same as the payload field name
            transactional_message_id="transactional_message_id",
            to="to",
            identifiers="identifiers",
            headers="headers",
            reply_to="reply_to",
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
