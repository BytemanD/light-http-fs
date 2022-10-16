
from lhfs.core.rpc import base

import zerorpc


class ZeroRpcServer(base.BaseRpcServer):

    def init_server(self):
        self._server = zerorpc.Server(self.manager)
        self.rpc_server.bind(self.transport)

    @property
    def transport(self):
        return f'tcp://{self.host}:{self.port}'

    def _start(self):
        self._server.run()

    def _stop(self):
        self._server.stop()
        self._server.close()


class ZeroRpcClient(base.BaseRpcClient):

    def init_client(self):
        return zerorpc.Client(self.transport)
