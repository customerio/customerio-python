from .client_base import ClientBase, CustomerIOException
from collections import namedtuple

Region = namedtuple('Region', ['name', 'track_host', 'api_host'])

RegionUS = Region('us', 'track.customer.io', 'api.customer.io')
RegionEU = Region('eu', 'track-eu.customer.io', 'api-eu.customer.io')
