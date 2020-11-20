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


from .client_base import CustomerIOException
from .track import CustomerIO
from .api import APIClient
