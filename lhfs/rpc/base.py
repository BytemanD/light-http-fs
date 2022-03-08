import abc

import gevent


class BaseRpcServer(object):

    def __init__(self, manager, host='0.0.0.0', port=8080):
        self.manager = manager
        self.host = host
        self.port = port
        self._server = None
        self._start_func = None
        self.init_server()

    @abc.abstractmethod
    def init_server(self):
        pass

    def start(self, daemon=False):
        if daemon:
            gevent.spawn(self._start_func)
        else:
            self._start_func()

    @abc.abstractproperty
    def transport(self):
        pass


class  BaseRpcClient(object):

    def __init__(self, transport):
        self.transport = transport
        self.client = self.init_client()

    @abc.abstractmethod
    def init_client(self):
        pass

    def get_nodes(self, host):
        return self.client.get_nodes(host)

    def ls(self, path, show_all=False):
        return self.client.ls(path, show_all)

    def mkdir(self, path):
        return self.client.mkdir(path)

    def rm(self, path, force=False):
        return self.client.rm(path, force)

    def rename(self, path, new_name):
        return self.client.rename(path, new_name)

    def disk_usage(self):
        return self.client.disk_usage()

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
