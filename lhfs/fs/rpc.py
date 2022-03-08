import contextlib
import zerorpc

from lhfs.common import conf
from lhfs.common import exception

CONF = conf.CONF


class RpcClient(object):

    def __init__(self, endpoint=None):
        self.client = zerorpc.Client()
        self.client.connect(endpoint or CONF.lhfs.master_rpc)

    def get_nodes(self, host):
        return self.client.get_nodes(host)

    def ls(self, path):
        return self.client.ls(path)

    def du(self):
        return self.client.disk_usage()

    def node_update(self, node):
        return self.client.node_update(node)


@contextlib.contextmanager
def with_node_rpc(node_name):

    master = RpcClient()
    nodes = master.get_nodes(node_name)
    if not nodes:
        raise exception.NodeNotExists(node=node_name)
    node = nodes[0]
    if node.get('hostname') == node_name:
        yield master
    else:
        node_rpc = RpcClient(endpoint=node.get('rpc_url'))
        yield node_rpc
