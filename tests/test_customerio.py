from customerio import CustomerIO, CustomerIOException
from tests.server import HTTPSTestCase


class TestCustomerIO(HTTPSTestCase):
    '''Starts server which the client connects to in the following tests'''

    def test_client_connection_handling(self):
        retries = 5
        cio = CustomerIO(
            site_id="siteid",
            api_key="apikey",
            host=self.server.server_address[0],
            port=self.server.server_port,
            retries=retries)

        # should not raise exception as i should be less than retries and 
        # therefore the last request should return a valid response
        for i in xrange(retries):
            cio.identify(i, fail_count=i)

        # should raise expection as we get invalid responses for all retries
        with self.assertRaises(CustomerIOException):
            cio.identify(retries, fail_count=retries)


if __name__ == '__main__':
    unittest.main()