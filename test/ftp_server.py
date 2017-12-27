from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

# from test.fixture_tools import PYFTPSYNC_TEST_FOLDER, PYFTPSYNC_TEST_FTP_URL


authorizer = DummyAuthorizer()
authorizer.add_user("tester", "secret", "/Users/martin/test_pyftpsync/remote", perm="elradfmwMT")
authorizer.add_anonymous("/Users/martin/test_pyftpsync/remote")

handler = FTPHandler
handler.authorizer = authorizer

server = FTPServer(("127.0.0.1", 21), handler)
server.serve_forever()
