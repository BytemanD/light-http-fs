import inspect

import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer


from easy2use.common import log

from lhfs.rpc import base

LOG = log.getLogger(__name__)


class XMLRpcServer(base.BaseRpcServer):

    def init_server(self):
        LOG.debug('init xml rpc server %s:%s ...', self.host, self.port)
        self._server = SimpleXMLRPCServer((self.host, self.port),
                                          allow_none=True,
                                          logRequests=True)
        self._start_func = self._server.serve_forever
        for name, func in inspect.getmembers(self.manager,
                                             predicate=inspect.ismethod):
            if name.startswith('_'):
                continue
            self._server.register_function(func)

    @property
    def transport(self):
        return 'http://{}:{}'.format(self.host, self.port)


class XMLRpcClient(base.BaseRpcClient):

    def init_client(self):
        return xmlrpclib.ServerProxy(self.transport, allow_none=True)
