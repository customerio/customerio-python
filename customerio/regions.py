class Regions:
    US = 'us'
    EU = 'eu'

    @staticmethod
    def api_host_for(region):
        return {
            'us': 'api.customer.io',
            'eu': 'api-eu.customer.io',
        }[region]

    @staticmethod
    def track_host_for(region):
        return {
            'us': 'track.customer.io',
            'eu': 'track-eu.customer.io',
        }[region]
