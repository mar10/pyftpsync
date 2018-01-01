"""
Run like
    $ python -m test.ftp_server
"""
import os

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

from .fixture_tools import PYFTPSYNC_TEST_FOLDER

directory = os.path.join(PYFTPSYNC_TEST_FOLDER, "remote")

authorizer = DummyAuthorizer()
authorizer.add_user("tester", "secret", directory, perm="elradfmwMT")
authorizer.add_anonymous(directory, perm="elradfmwMT")

handler = FTPHandler
handler.authorizer = authorizer

server = FTPServer(("127.0.0.1", 8021), handler)
server.serve_forever()
