from collections import namedtuple

Region = namedtuple('Region', ['name', 'track_host', 'api_host'])

class Regions:
    US = Region('us', 'track.customer.io', 'api.customer.io')
    EU = Region('eu', 'track-eu.customer.io', 'api-eu.customer.io')
