"""
Implements a single client for the Track and App APIs, authenticated with one key.
"""

import re
from functools import wraps
from urllib.parse import urlsplit

from requests.auth import AuthBase

from .api import APIClient
from .client_base import CustomerIOException, KeyCapabilityError
from .regions import Region, Regions
from .track import CustomerIO

# Keys in the shared format look like `{type}_{us|eu}_{random}_{checksum}`, where type
# is `pk` (public) or `sk` (secret). The server checks the checksum; the client only
# reads the prefix to pick a host and spot public keys.
KEY_PREFIX = re.compile(r"^([a-z]{2})_(us|eu)_")

CAPABILITY_ACTIONS = {
    "track": "send tracking data",
    "transactional": "send transactional messages",
}


class _BearerAuth(AuthBase):
    """Sends the key as a Bearer token. Set as ``session.auth`` so Requests never swaps
    in Basic auth from a matching ``.netrc`` entry."""

    def __init__(self, key):
        self.key = key

    def __call__(self, request):
        request.headers["Authorization"] = f"Bearer {self.key}"
        return request


class _BearerTrackClient(CustomerIO):
    """Track API client that sends the key as a Bearer token instead of Basic auth."""

    def _build_session(self):
        session = super()._build_session()
        session.auth = _BearerAuth(self.api_key)
        return session


def _guard(capability):
    """Re-raises a 401 or 403 as a KeyCapabilityError so a refusal is never a bare
    auth failure."""

    def decorator(method):
        @wraps(method)
        def wrapper(*args, **kwargs):
            try:
                return method(*args, **kwargs)
            except KeyCapabilityError:
                raise
            except CustomerIOException as e:
                status = getattr(e, "status_code", None)
                if status not in (401, 403):
                    raise
                message = (
                    f"The request to {CAPABILITY_ACTIONS[capability]} was refused ({status}): "
                    f"{_server_message(e.response)}. Check the key, its permissions, the IP "
                    "allowlist and the workspace status."
                )
                raise KeyCapabilityError(capability, message, status_code=status) from e

        return wrapper

    return decorator


def _server_message(response):
    try:
        return response.json()["meta"]["error"]
    except Exception:
        return response.text


class Client:
    """One client for tracking and transactional messages, authenticated with a single key.

    Tracking methods (``identify``, ``track``, ``track_anonymous``, ``pageview``) go to
    the Track API; ``send_*`` methods go to the App API. Both send the key as a Bearer
    token. For ``sk_us_…`` / ``sk_eu_…`` keys the region comes from the key; an explicit
    ``region`` wins. Legacy keys default to ``Regions.US``.

    When a call is refused, the method raises a
    :class:`KeyCapabilityError`: before the request when the key's type says so (a
    public ``pk_`` key can't send transactional messages), otherwise when the server
    answers 401 or 403.

    Other Track and App API methods are on ``track_client`` and ``api_client``.
    """

    def __init__(
        self,
        api_key,
        region=None,
        track_url=None,
        api_url=None,
        retries=3,
        timeout=10,
        backoff_factor=0.02,
        use_connection_pooling=True,
    ):
        if not api_key:
            raise CustomerIOException("api_key is required")
        if region is not None and not isinstance(region, Region):
            raise CustomerIOException("invalid region provided")

        match = KEY_PREFIX.match(api_key)
        self._key_kind = match.group(1) if match else "legacy"
        key_region = (Regions.EU if match.group(2) == "eu" else Regions.US) if match else None
        self.region = region or key_region or Regions.US

        options = dict(
            retries=retries,
            timeout=timeout,
            backoff_factor=backoff_factor,
            use_connection_pooling=use_connection_pooling,
        )

        track_host = track_port = track_prefix = None
        if track_url:
            parts = urlsplit(track_url)
            if parts.scheme != "https":
                raise CustomerIOException("track_url must start with https://")
            track_host, track_port = parts.hostname, parts.port
            # Requests rejects an IPv6 literal without its brackets.
            if track_host and ":" in track_host:
                track_host = f"[{track_host}]"
            # A bare "/" path falls back to the default /api/v1 prefix.
            track_prefix = parts.path.rstrip("/") or None

        #: Track API client, authenticated with the key as a Bearer token.
        self.track_client = _BearerTrackClient(
            api_key=api_key,
            host=track_host,
            port=track_port,
            url_prefix=track_prefix,
            region=self.region,
            **options,
        )
        self._api_client = APIClient(api_key, url=api_url, region=self.region, **options)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        try:
            self.track_client.close()
        finally:
            self._api_client.close()

    @property
    def api_client(self):
        """App API client, authenticated with the key.

        Raises :class:`KeyCapabilityError` if the key is a public ``pk_`` key.
        """
        if self._key_kind == "pk":
            raise KeyCapabilityError(
                "transactional",
                "This key can't use the App API: public keys (pk_) are for tracking only. "
                "Use a secret key (sk_).",
            )
        return self._api_client

    @_guard("track")
    def identify(self, id, **kwargs):
        """Create or update a person. See :meth:`CustomerIO.identify`."""
        return self.track_client.identify(id, **kwargs)

    @_guard("track")
    def track(self, customer_id, name, data=None, id=None, timestamp=None):
        """Track an event for a person. See :meth:`CustomerIO.track`."""
        return self.track_client.track(customer_id, name, data=data, id=id, timestamp=timestamp)

    @_guard("track")
    def track_anonymous(self, anonymous_id, name, data=None, id=None, timestamp=None):
        """Track an event for an anonymous visitor. See :meth:`CustomerIO.track_anonymous`."""
        return self.track_client.track_anonymous(
            anonymous_id, name, data=data, id=id, timestamp=timestamp
        )

    @_guard("track")
    def pageview(self, customer_id, page, **data):
        """Track a page view for a person. See :meth:`CustomerIO.pageview`."""
        return self.track_client.pageview(customer_id, page, **data)

    @_guard("transactional")
    def send_email(self, request):
        """Send a transactional email. See :meth:`APIClient.send_email`."""
        return self.api_client.send_email(request)

    @_guard("transactional")
    def send_push(self, request):
        """Send a transactional push. See :meth:`APIClient.send_push`."""
        return self.api_client.send_push(request)

    @_guard("transactional")
    def send_sms(self, request):
        """Send a transactional SMS. See :meth:`APIClient.send_sms`."""
        return self.api_client.send_sms(request)

    @_guard("transactional")
    def send_whatsapp(self, request):
        """Send a transactional WhatsApp message. See :meth:`APIClient.send_whatsapp`."""
        return self.api_client.send_whatsapp(request)

    @_guard("transactional")
    def send_inbox_message(self, request):
        """Send a transactional inbox message. See :meth:`APIClient.send_inbox_message`."""
        return self.api_client.send_inbox_message(request)

    @_guard("transactional")
    def send_in_app(self, request):
        """Send a transactional in-app message. See :meth:`APIClient.send_in_app`."""
        return self.api_client.send_in_app(request)
