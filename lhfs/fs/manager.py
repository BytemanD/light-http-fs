import os
import time
import mimetypes
import abc

from easy2use.common import log
from easy2use import fs
from easy2use import structure
from easy2use.system import Disk
from easy2use.system import OS

from lhfs.common import conf
from lhfs.common import constants
from lhfs.common import exception
from lhfs.common import utils
from lhfs.fs import objects

CONF = conf.CONF


NODE_MANAGER = None
LOG = log.getLogger(__name__)


rpc_class = {
    'xmlrpc': ('xml_rpc.XMLRpcServer', 'xml_rpc.XMLRpcClient', ),
    'zerorpc': ('zero_rpc.ZeroRpcServer', 'zero_rpc.ZeroRpcClient', )
}


class FSManager(object):

    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.search_history = structure.LastNList(10)
        LOG.info('root path is %s', self.root)

    def make_path_obj(self, logic_path):
        return objects.LogicPath(self.root, logic_path)

    @utils.remotable
    def is_file(self, path):
        lp = objects.LogicPath(self.root, path)
        return lp.exists() and not lp.is_dir()

    @utils.remotable
    def get_abs_path(self, path):
        # if isinstance(path, str):
        #     return os.path.join(self.root, path)
        # else:
        #     # path is a list
        #     return os.path.join(self.root, *path)
        lp = objects.LogicPath(self.root, path)
        return lp.abs_path()

    def path_exists(self, path):
        return os.path.exists(self.get_abs_path(path))

    def get_path_dict(self, path):
        lp = objects.LogicPath(self.root, path)
        return lp.dict_info()

    def editable(self, path):
        abs_path = self.get_abs_path(path)
        if os.path.isfile(abs_path):
            t, _ = mimetypes.guess_type(abs_path)
            if t in ['text/plain', 'application/x-sh']:
                return True
        return False

    @utils.remotable
    def mkdir(self, path):
        lp = objects.LogicPath(self.root, path)
        if lp.exists():
            raise exception.FileExists(path=path)
        lp.mkdir()

    @utils.remotable
    def ensure_parent_dir(self, path):
        lp = objects.LogicPath(self.root, path)
        lp.ensure_parent_dir()

    @utils.remotable
    def rename(self, path, new_name):
        LOG.info('rename: %s to %s', path, new_name)
        lp = objects.LogicPath(self.root, path)
        lp.rename(new_name)

    @utils.remotable
    def rm(self, path, force):
        LOG.info('rm(recursive=%s): %s', force, path)
        lp = objects.LogicPath(self.root, path)
        lp.delete(recursive=force)
        LOG.debug('rm success: %s', path)

    def listdir(self, path):
        lp = objects.LogicPath(self.root, path)
        return os.listdir(lp.abs_path())

    @staticmethod
    def safe_path(path):
        if not path:
            return ['.']
        if isinstance(path, list):
            if len(path) > 0 and path[0] == '/':
                return path[1:]
            return path
        else:
            return path.split('/')

    @utils.remotable
    def ls(self, path, show_all):
        lp = objects.LogicPath(self.root, path)
        return lp.ls(show_all=show_all)

    @utils.remotable
    def get_file_content(self, path):
        lp = objects.LogicPath(self.root, path)
        return lp.file_content()

    def save_file(self, path, fo):
        save_path = '{}/{}'.format(path, fo.filename)
        save_dir = '{}/{}'.format(path, os.path.dirname((fo.filename)))
        dir_lp = objects.LogicPath(self.root, save_dir)
        if not dir_lp.exists():
            dir_lp.mkdir()
        file_lp = objects.LogicPath(self.root, save_path)
        file_lp.save(fo)

    @utils.remotable
    def disk_usage(self):
        sdiskusage = Disk.usage(self.root)
        LOG.debug('get disk usage: %s', sdiskusage)
        return objects.DiskUsageKB(
            total=sdiskusage.total / constants.Unit.KB.value,
            used=sdiskusage.used / constants.Unit.KB.value,
            free=sdiskusage.free / constants.Unit.KB.value,
            percent=sdiskusage.percent)

    def abs_to_logic(self, abs_path):
        logic_path = abs_path[len(self.root):]
        if OS.is_windows():
            return '/'.join(logic_path.split('\\'))
        else:
            return logic_path

    def _split_path(self, path_string):
        """Parse string path to list
        """
        if OS.is_windows():
            return path_string.split('\\')
        return path_string.split('/')

    @utils.remotable
    def find(self, partern):
        """Find files by partern name
        E.g. *.py, setup.py
        """
        matched_pathes = []
        for dirPath, name in fs.find(self.root, partern):
            logic_dir = self.abs_to_logic(dirPath)
            lp = objects.LogicPath(self.root, '{}/{}'.format(logic_dir, name))
            item = lp.dict_info()
            item.pardir = logic_dir
            matched_pathes.append(item.to_dict())
        if partern not in self.search_history.all():
            self.search_history.append(partern)
        return matched_pathes

    @utils.remotable
    def get_search_history(self):
        return self.search_history.all()

    @utils.remotable
    def file_size(self, path):
        lp = objects.LogicPath(self.root, path)
        return lp.size()

    def zip_path(self, path):
        lp = objects.LogicPath(self.root, path)
        return fs.zip_files(lp.abs_path())


class BaseNodeManager(FSManager):
    RUN_RPC_SERVER_AS_DAEMON = False

    def __init__(self, root, node_type, rpc_server=None,
                 ssh_user=None, ssh_password=None):
        super(BaseNodeManager, self).__init__(root)
        self.node = objects.Node(
            type=node_type,
            transport=rpc_server and rpc_server.transport or None,
            ssh_user=ssh_user, ssh_password=ssh_password)
        self.rpc_server = rpc_server
        LOG.info('inited %s', self.node.type)

    @abc.abstractmethod
    def heartbeat(self):
        pass

    def start_rpc(self):
        if not self.rpc_server:
            return
        LOG.info('starting rpc server: %s', self.rpc_server.transport)
        self.rpc_server.start(daemon=self.RUN_RPC_SERVER_AS_DAEMON)
        LOG.info('started rpc server at %s', self.rpc_server.transport)


class MasterManager(BaseNodeManager):
    RUN_RPC_SERVER_AS_DAEMON = True

    def __init__(self, root, **kwargs):
        super(MasterManager, self).__init__(
            root, constants.MASTER,
            rpc_server=utils.get_rpc_server(self, host=CONF.lhfs.rpc_host,
                                            port=CONF.lhfs.rpc_port),
            **kwargs)
        self.nodes = {}
        self.heartbeats = {}
        self.heartbeat()

    def node_update(self, node_dict):
        node = objects.Node.from_dict(node_dict)
        exited_node = self.nodes.get(node.hostname)
        if exited_node and node.ip != exited_node.ip:
            raise exception.ConflictNode(node=node.get('hostname'),
                                         exists=exited_node.ip)

        LOG.debug('update node: %s', node)
        node.heartbeat = time.time()
        self.nodes[node.hostname] = node

    @utils.timer(interval=CONF.heartbeat_interval)
    def heartbeat(self):
        LOG.debug('node %s heartbeat', self.node.hostname)
        self.node_update(self.node.to_dict())

    def list_nodes(self):
        nodes = list(self.nodes.values())
        for node in nodes:
            node.status = self.is_node_active and constants.ACTIVE \
                or constants.DOWN
        return nodes

    def get_node(self, hostname):
        return self.nodes.get(hostname)

    def is_node_active(self, node):
        if node.heartbeat is None:
            return False
        return time.time() - node.heartbeat < CONF.heartbeat_alive


class SlaveManager(BaseNodeManager):

    def __init__(self, root, **kwargs):
        super(SlaveManager, self).__init__(
            root, constants.SLAVE,
            rpc_server=utils.get_rpc_server(self, host=CONF.lhfs.rpc_host,
                                            port=CONF.lhfs.rpc_port),
            **kwargs)
        self.master = utils.get_rpc_client(transport=CONF.lhfs.master_rpc)

    @utils.timer(interval=CONF.heartbeat_interval)
    def heartbeat(self):
        LOG.debug('node %s heartbeat', self.node.hostname)
        self.master.node_update(self.node.to_dict())
