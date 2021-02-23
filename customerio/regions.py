from .client_base import ClientBase, CustomerIOException

class Regions:
    US = 'us'
    EU = 'eu'

    @staticmethod
    def api_host_for(region):
        if region not in [Regions.US, Regions.EU]:
            raise CustomerIOException('region must be one of {us} or {eu}'.format(us=Regions.US, eu=Regions.EU))

        return {
            'us': 'api.customer.io',
            'eu': 'api-eu.customer.io',
        }[region]

    @staticmethod
    def track_host_for(region):
        if region not in [Regions.US, Regions.EU]:
            raise CustomerIOException('region must be one of {us} or {eu}'.format(us=Regions.US, eu=Regions.EU))

        return {
            'us': 'track.customer.io',
            'eu': 'track-eu.customer.io',
        }[region]
