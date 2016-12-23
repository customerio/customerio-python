try:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
except ImportError:
    from http.server import BaseHTTPRequestHandler, HTTPServer

from functools import wraps
from random import randint

import json
import ssl
import time
import threading
import unittest

def sslwrap(func):
    @wraps(func)
    def bar(*args, **kw):
        kw['ssl_version'] = ssl.PROTOCOL_TLSv1
        return func(*args, **kw)
    return bar

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
        self.end_headers()

    def do_POST(self):
        self.send_response(200)
        self.end_headers()

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
        # hack needed to setup ssl server
        ssl.wrap_socket = sslwrap(ssl.wrap_socket)
        # upgrade to https
        cls.server.socket = ssl.wrap_socket(cls.server.socket,
            certfile='./tests/server.pem',
            server_side=True)
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
