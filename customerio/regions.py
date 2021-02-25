from collections import namedtuple

Region = namedtuple('Region', ['name', 'track_host', 'api_host'])

Regions = {
    'us': Region('us', 'track.customer.io', 'api.customer.io'),
    'eu': Region('eu', 'track-eu.customer.io', 'api-eu.customer.io')
}
