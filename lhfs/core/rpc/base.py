import abc
import logging

import gevent

from lhfs.core import objects

LOG = logging.getLogger(__name__)


class BaseRpcServer(object):

    def __init__(self, manager, host='0.0.0.0', port=8080):
        self.manager = manager
        self.host = host
        self.port = port
        self._server = None
        self.init_server()

    @abc.abstractmethod
    def init_server(self):
        pass

    def start(self, daemon=False):
        LOG.info('starting xmlrpc server with daemon: %s', daemon)
        if daemon:
            gevent.spawn(self._start)
        else:
            self._start()

    @abc.abstractproperty
    def transport(self):
        pass

    def stop(self):
        LOG.info('stopping rpc server')
        self._stop()
        LOG.info('stopped rpc server')

    @abc.abstractmethod
    def _start(self):
        pass

    @abc.abstractmethod
    def _stop(self):
        pass


class BaseRpcClient(object):

    def __init__(self, transport):
        self.transport = transport
        self.client = self.init_client()

    @abc.abstractmethod
    def init_client(self):
        pass

    def list_nodes(self):
        node_list = self.client.list_nodes()
        return [objects.Node.from_dict(node_dict) for node_dict in node_list]

    def get_master_nodes(self):
        node_dict = self.client.get_master_nodes()
        return node_dict and objects.Node.from_dict(node_dict) or None

    def get_node(self, hostname):
        node_dict = self.client.get_node(hostname)
        return node_dict and objects.Node.from_dict(node_dict) or None

    def ls(self, path, show_all=False):
        items = self.client.ls(path, show_all)
        return [objects.DirItem.from_dict(item) for item in items]

    def mkdir(self, path):
        return self.client.mkdir(path)

    def rm(self, path, force=False):
        return self.client.rm(path, force)

    def rename(self, path, new_name):
        return self.client.rename(path, new_name)

    def disk_usage(self):
        return objects.DiskUsageKB.from_dict(self.client.disk_usage())

    def node_update(self, node):
        return self.client.node_update(node)

    def find(self, partern):
        return self.client.find(partern)

    def get_search_history(self):
        return self.client.get_search_history()

    def get_abs_path(self, path):
        return self.client.get_abs_path(path)

    def file_size(self, path):
        return self.client.file_size(path)

    def ensure_parent_dir(self, path):
        return self.client.ensure_parent_dir(path)
