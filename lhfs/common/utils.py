import logging
import time
import functools
from threading import Timer

from easy2use.common import pkg
from easy2use.pysshpass import ssh

from lhfs.common import conf
from lhfs.common import constants
from lhfs.common import exception

CONF = conf.CONF


NODE_MANAGER = None
LOG = logging.getLogger(__name__)


def timer(interval=1):

    def timer_wrapper(func):

        def func_wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as e:
                LOG.error(e)
            t = Timer(interval, func_wrapper, args=args, kwargs=kwargs)
            t.start()
        return func_wrapper

    return timer_wrapper


def get_rpc_server(manager, host='0.0.0.0', port=8080):
    driver_cls = pkg.import_class(
        constants.RPC_CLASS_MAPPING.get(CONF.lhfs.rpc_driver)[0])
    return driver_cls(manager, host=host, port=port)


def get_rpc_client(transport=None):
    driver_cls = pkg.import_class(
        constants.RPC_CLASS_MAPPING.get(CONF.lhfs.rpc_driver)[1])
    return driver_cls(transport)


def remotable(func):
    """Execute func on local or remote with rpc.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        host = kwargs.pop('host', None)
        if not host or (hasattr(self, 'node') and self.node.hostname == host):
            return func(self, *args, **kwargs)
        elif hasattr(self, 'nodes'):
            if host not in self.nodes:
                raise exception.NodeNotExists(node=host)
            node = self.nodes.get(host)
            if time.time() - node.get('heartbeat') >= CONF.heartbeat_alive:
                raise exception.NodeInactive(node=host)
            client = get_rpc_client(transport=node.get('transport'))
            return getattr(client, func.__name__)(*args, **kwargs)

    return wrapper


def get_reqeust_arg(flask_req, arg, default=None):
    arg_value_map = {'NULL': None, 'FALSE': False, 'TRUE': True, }
    value = flask_req.args.get(arg, default)
    if value is None or value == default:
        return value
    if str(value.upper()) in arg_value_map:
        return arg_value_map[str(value.upper())]
    return value


def stream_generator(remote_node, abs_path):
    sshclient = ssh.SSHClient(remote_node['ip'], remote_node['ssh_user'],
                              remote_node['ssh_password'])
    sshclient._connect()
    sftp = sshclient.client.open_sftp()
    file_size = sftp.stat(abs_path).st_size

    with sftp.open(abs_path, "rb") as fr:
        fr.prefetch(file_size)
        while True:
            data = fr.read(32768)
            if not data:
                break
            yield data


def human_size(size):
    if size is None:
        return size
    if size >= constants.Unit.GB.value:
        return f'{size / constants.Unit.GB.value:.2f} GB'
    elif size >= constants.Unit.MB.value:
        return f'{size / constants.Unit.MB.value:.2f} MB'
    elif size >= constants.Unit.KB.value:
        return f'{size / constants.Unit.KB.value:.2f} KB'
    else:
        return f'{size:.2f}  B'
