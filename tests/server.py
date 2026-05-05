try:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
except ImportError:
    from http.server import BaseHTTPRequestHandler, HTTPServer

from random import randint
import json
import ssl
import time
import threading
import unittest

def create_ssl_context():
    """Create SSL context for Python 3.12+ compatibility"""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    # Disable hostname and certificate verification for self-signed certs
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    # Allow weaker ciphers for test compatibility
    try:
        context.set_ciphers('DEFAULT@SECLEVEL=1')
    except ssl.SSLError:
        # Fall back if the cipher string is not supported
        pass
    return context

request_counts = dict()

class Handler(BaseHTTPRequestHandler):
    '''Handler definition for the testing server instance.

    This handler returns without setting response status code which causes
    httplib to raise BadStatusLine exception.
    The handler reads the post body and fails for the `fail_count` specified.
    After sending specified number of bad responses will sent a valid response.
    '''
    def do_DELETE(self):
        self.send_response(200)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_POST(self):
        response_body = bytes("{}", "utf-8")
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def do_PUT(self):
        global request_counts

        # extract params
        _id = self.path.split("/")[-1]
        content_len = int(self.headers.get('content-length', 0))
        params = json.loads(self.rfile.read(content_len).decode('utf-8'))
        fail_count = params.get('fail_count', 0)

        # retrieve number of requests already served
        processed = request_counts.get(_id, 0)
        if processed > fail_count:
            # return a valid response
            self.send_response(200)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return

        # increment number of requests and return invalid response
        request_counts[_id] = processed + 1
        return

    # Silence the server so test output is not cluttered
    def log_message(self, format, *args):
        return


class HTTPSTestCase(unittest.TestCase):
    '''Test case class that starts up a https server and exposes it via the `server` attribute.

    The testing server is only created in the setUpClass method so that multiple
    tests can use the same server instance. The server is started in a separate
    thread and once the tests are completed the server is shutdown and cleaned up.
    '''

    @classmethod
    def setUpClass(cls):
        # create a server
        cls.server = HTTPServer(("localhost", 0), Handler)
        # create SSL context for Python 3.12+ compatibility
        context = create_ssl_context()
        context.load_cert_chain('./tests/server.pem')
        # upgrade to https
        cls.server.socket = context.wrap_socket(cls.server.socket, server_side=True)
        # start server instance in new thread
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.start()
        # Wait a bit for the server to bind to port
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        # shutdown server and close thread
        cls.server.shutdown()
        cls.server.socket.close()
        cls.server_thread.join()
