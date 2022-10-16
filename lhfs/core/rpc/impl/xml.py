import inspect
import logging

from xmlrpc import client
from xmlrpc.server import SimpleXMLRPCServer

from lhfs.core.rpc import base

LOG = logging.getLogger(__name__)


class XMLRpcServer(base.BaseRpcServer):

    def init_server(self):
        self._server = SimpleXMLRPCServer((self.host, self.port),
                                          allow_none=True,
                                          logRequests=True)
        for name, func in inspect.getmembers(self.manager,
                                             predicate=inspect.ismethod):
            if name.startswith('_'):
                continue
            self._server.register_function(func)

    @property
    def transport(self):
        return f'http://{self.host}:{self.port}'

    def _start(self):
        self._server.serve_forever()

    def _stop(self):
        self._server.shutdown()


class XMLRpcClient(base.BaseRpcClient):

    def init_client(self):
        return client.ServerProxy(self.transport, allow_none=True)
