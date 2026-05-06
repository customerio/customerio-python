"""
Implements the client that interacts with Customer.io's App API using app keys.
"""

import base64
import json

from .client_base import ClientBase, CustomerIOException
from .regions import Region, Regions


def _payload_from_fields(source, field_map):
    return {
        name: value
        for field, name in field_map.items()
        if (value := getattr(source, field, None)) is not None
    }


COMMON_MESSAGE_FIELD_MAP = {
    "transactional_message_id": "transactional_message_id",
    "identifiers": "identifiers",
    "disable_message_retention": "disable_message_retention",
    "queue_draft": "queue_draft",
    "message_data": "message_data",
    "send_at": "send_at",
    "language": "language",
}

EMAIL_FIELD_MAP = COMMON_MESSAGE_FIELD_MAP | {
    # from is a reserved keyword, so the object field is `_from`.
    "_from": "from",
    "to": "to",
    "headers": "headers",
    "reply_to": "reply_to",
    "bcc": "bcc",
    "subject": "subject",
    "preheader": "preheader",
    "body": "body",
    "body_plain": "body_plain",
    "body_amp": "body_amp",
    "fake_bcc": "fake_bcc",
    "send_to_unsubscribed": "send_to_unsubscribed",
    "tracked": "tracked",
    "attachments": "attachments",
    "disable_css_preprocessing": "disable_css_preprocessing",
}

PUSH_FIELD_MAP = COMMON_MESSAGE_FIELD_MAP | {
    "to": "to",
    "send_to_unsubscribed": "send_to_unsubscribed",
    "title": "title",
    "message": "message",
    "image_url": "image_url",
    "link": "link",
    "custom_data": "custom_data",
    "custom_payload": "custom_payload",
    "device": "custom_device",
    "sound": "sound",
}

SMS_FIELD_MAP = COMMON_MESSAGE_FIELD_MAP | {
    "to": "to",
    "send_to_unsubscribed": "send_to_unsubscribed",
}

INBOX_FIELD_MAP = COMMON_MESSAGE_FIELD_MAP
IN_APP_FIELD_MAP = COMMON_MESSAGE_FIELD_MAP


class APIClient(ClientBase):
    def __init__(
        self,
        key,
        url=None,
        region=Regions.US,
        retries=3,
        timeout=10,
        backoff_factor=0.02,
        use_connection_pooling=True,
    ):
        if not isinstance(region, Region):
            raise CustomerIOException("invalid region provided")

        self.key = key
        self.url = url or f"https://{region.api_host}"
        super().__init__(
            retries=retries,
            timeout=timeout,
            backoff_factor=backoff_factor,
            use_connection_pooling=use_connection_pooling,
        )

    def send_email(self, request):
        if isinstance(request, SendEmailRequest):
            request = request._to_dict()
        resp = self.send_request("POST", self.url + "/v1/send/email", request)
        return json.loads(resp)

    def send_push(self, request):
        if isinstance(request, SendPushRequest):
            request = request._to_dict()
        resp = self.send_request("POST", self.url + "/v1/send/push", request)
        return json.loads(resp)

    def send_sms(self, request):
        if isinstance(request, SendSMSRequest):
            request = request._to_dict()
        resp = self.send_request("POST", self.url + "/v1/send/sms", request)
        return json.loads(resp)

    def send_inbox_message(self, request):
        if isinstance(request, SendInboxMessageRequest):
            request = request._to_dict()
        resp = self.send_request("POST", self.url + "/v1/send/inbox_message", request)
        return json.loads(resp)

    def send_in_app(self, request):
        if isinstance(request, SendInAppRequest):
            request = request._to_dict()
        resp = self.send_request("POST", self.url + "/v1/send/in_app", request)
        return json.loads(resp)

    def _build_session(self):
        session = super()._build_session()
        session.headers["Authorization"] = f"Bearer {self.key}"

        return session


class SendEmailRequest:
    """An object with all the options available for triggering a transactional email message."""

    def __init__(
        self,
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
        disable_css_preprocessing=None,
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
        self.disable_css_preprocessing = disable_css_preprocessing
        self.send_at = send_at
        self.language = language

    def attach(self, name, content, encode=True):
        """Helper method to add base64-encoded attachments."""
        if not self.attachments:
            self.attachments = {}

        if name in self.attachments:
            raise CustomerIOException(f"attachment {name} already exists")

        if encode:
            if isinstance(content, str):
                content = base64.b64encode(content.encode("utf-8")).decode()
            else:
                content = base64.b64encode(content).decode()

        self.attachments[name] = content

    def _to_dict(self):
        """Build a request payload from the object."""
        return _payload_from_fields(self, EMAIL_FIELD_MAP)


class SendPushRequest:
    """An object with all the options available for triggering a transactional push message."""

    def __init__(
        self,
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
        sound=None,
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
        """Build a request payload from the object."""
        return _payload_from_fields(self, PUSH_FIELD_MAP)


class SendSMSRequest:
    """An object with all the options available for triggering a transactional SMS message."""

    def __init__(
        self,
        transactional_message_id=None,
        to=None,
        identifiers=None,
        disable_message_retention=None,
        send_to_unsubscribed=None,
        queue_draft=None,
        message_data=None,
        send_at=None,
        language=None,
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

    def _to_dict(self):
        """Build a request payload from the object."""
        return _payload_from_fields(self, SMS_FIELD_MAP)


class SendInboxMessageRequest:
    """An object with all the options available for triggering a transactional inbox message."""

    def __init__(
        self,
        transactional_message_id=None,
        identifiers=None,
        disable_message_retention=None,
        queue_draft=None,
        message_data=None,
        send_at=None,
        language=None,
    ):
        self.transactional_message_id = transactional_message_id
        self.identifiers = identifiers
        self.disable_message_retention = disable_message_retention
        self.queue_draft = queue_draft
        self.message_data = message_data
        self.send_at = send_at
        self.language = language

    def _to_dict(self):
        """Build a request payload from the object."""
        return _payload_from_fields(self, INBOX_FIELD_MAP)


class SendInAppRequest:
    """An object with all the options available for triggering a transactional in-app message."""

    def __init__(
        self,
        transactional_message_id=None,
        identifiers=None,
        disable_message_retention=None,
        queue_draft=None,
        message_data=None,
        send_at=None,
        language=None,
    ):
        self.transactional_message_id = transactional_message_id
        self.identifiers = identifiers
        self.disable_message_retention = disable_message_retention
        self.queue_draft = queue_draft
        self.message_data = message_data
        self.send_at = send_at
        self.language = language

    def _to_dict(self):
        """Build a request payload from the object."""
        return _payload_from_fields(self, IN_APP_FIELD_MAP)
