"""
Implements the client that interacts with Customer.io's App API using app keys.
"""
import base64
import json
from .client_base import ClientBase, CustomerIOException
from .regions import Regions, Region

class APIClient(ClientBase):
    def __init__(self, key, url=None, region=Regions.US, retries=3, timeout=10, backoff_factor=0.02, use_connection_pooling=True):
        if not isinstance(region, Region):
            raise CustomerIOException('invalid region provided')

        self.key = key
        self.url = url or 'https://{host}'.format(host=region.api_host)
        ClientBase.__init__(self, retries=retries,
                            timeout=timeout, backoff_factor=backoff_factor, use_connection_pooling=use_connection_pooling)

    def send_email(self, request):
        if isinstance(request, SendEmailRequest):
            request = request._to_dict()
        resp = self.send_request('POST', self.url + "/v1/send/email", request)
        return json.loads(resp)

    def send_push(self, request):
        if isinstance(request, SendPushRequest):
            request = request._to_dict()
        resp = self.send_request('POST', self.url + "/v1/send/push", request)
        return json.loads(resp)

    # builds the session.
    def _build_session(self):
        session = super()._build_session()
        session.headers['Authorization'] = "Bearer {key}".format(key=self.key)

        return session

class SendEmailRequest(object):
    '''An object with all the options avaiable for triggering a transactional email message'''
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
            body_plain=None,
            body_amp=None,
            fake_bcc=None,
            disable_message_retention=None,
            send_to_unsubscribed=None,
            tracked=None,
            queue_draft=None,
            message_data=None,
            attachments=None,
            disable_css_preproceessing=None,
            send_at=None,
            language=None,
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
        self.body_plain = body_plain
        self.body_amp = body_amp
        self.fake_bcc = fake_bcc
        self.disable_message_retention = disable_message_retention
        self.send_to_unsubscribed = send_to_unsubscribed
        self.tracked = tracked
        self.queue_draft = queue_draft
        self.message_data = message_data
        self.attachments = attachments
        self.disable_css_preproceessing = disable_css_preproceessing
        self.send_at = send_at
        self.language = language

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
        '''Build a request payload from the object'''
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
            body_plain="body_plain",
            body_amp="body_amp",
            fake_bcc="fake_bcc",
            disable_message_retention="disable_message_retention",
            send_to_unsubscribed="send_to_unsubscribed",
            tracked="tracked",
            queue_draft="queue_draft",
            message_data="message_data",
            attachments="attachments",
            disable_css_preproceessing="disable_css_preproceessing",
            send_at="send_at",
            language="language",
        )

        data = {}
        for field, name in field_map.items():
            value = getattr(self, field, None)
            if value is not None:
                data[name] = value

        return data

class SendPushRequest(object):
    '''An object with all the options avaiable for triggering a transactional push message'''
    def __init__(self,
            transactional_message_id=None,
            to=None,
            identifiers=None,
            title=None,
            message=None,
            disable_message_retention=None,
            send_to_unsubscribed=None,
            queue_draft=None,
            message_data=None,
            send_at=None,
            language=None,
            image_url=None,
            link=None,
            custom_data=None,
            custom_payload=None,
            device=None,
            sound=None
        ):

        self.transactional_message_id = transactional_message_id
        self.to = to
        self.identifiers = identifiers
        self.disable_message_retention = disable_message_retention
        self.send_to_unsubscribed = send_to_unsubscribed
        self.queue_draft = queue_draft
        self.message_data = message_data
        self.send_at = send_at
        self.language = language

        self.title = title
        self.message = message
        self.image_url = image_url
        self.link = link
        self.custom_data = custom_data
        self.custom_payload = custom_payload
        self.device = device
        self.sound = sound

    def _to_dict(self):
        '''Build a request payload from the object'''
        field_map = dict(
            # field name is the same as the payload field name
            transactional_message_id="transactional_message_id",
            to="to",
            identifiers="identifiers",
            disable_message_retention="disable_message_retention",
            send_to_unsubscribed="send_to_unsubscribed",
            queue_draft="queue_draft",
            message_data="message_data",
            send_at="send_at",
            language="language",

            title="title",
            message="message",
            image_url="image_url",
            link="link",
            custom_data="custom_data",
            custom_payload="custom_payload",
            device="custom_device",
            sound="sound"
        )

        data = {}
        for field, name in field_map.items():
            value = getattr(self, field, None)
            if value is not None:
                data[name] = value

        return data
