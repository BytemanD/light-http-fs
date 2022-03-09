import zerorpc

from lhfs.rpc import base


class ZeroRpcServer(base.BaseRpcServer):

    def init_server(self):
        self._server = zerorpc.Server(self.manager)
        self._start_func = self._server.run
        # zerorpc.gevent.spawn(self.rpc_server.run)
        self.rpc_server.bind(self.transport)

    @property
    def transport(self):
        return 'tcp://{}:{}'.format(self.host, self.port)


class ZeroRpcClient(base.BaseRpcClient):

    def init_client(self):
        return zerorpc.Client(self.transport)
