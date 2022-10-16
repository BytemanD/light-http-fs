import os
import socket

from easy2use.globals import cfg

CONF = cfg.CONF
DEFAULT_HOST = socket.gethostname()

default_options = [
    cfg.BooleanOption('debug', default=False),
    cfg.IntOption('workers', default=None),
    cfg.Option('log_file', default=None),
    cfg.IntOption('heartbeat_interval', default=10),
    cfg.IntOption('heartbeat_alive', default=60),
]
api_options = [
    cfg.Option('host', default='{my_ip}'),
    cfg.IntOption('port', default=80),
    
]
lhfs_options = [
    cfg.Option('host', default=socket.gethostname()),
    cfg.Option('my_ip', default=socket.gethostbyname(DEFAULT_HOST)),
    cfg.Option('rpc_host', default='{my_ip}'),
    cfg.IntOption('rpc_port', default=9527),
    cfg.Option('root', default='./'),
    cfg.Option('rpc_driver', default='xmlrpc'),
    cfg.Option('master_rpc', default='http://{my_ip}:{rpc_port}'),
]

web_options = {
    cfg.BooleanOption('use_static_cdn', default=False),
    cfg.Option('theme', default='material'),
    # 'material', 'bootstrap'
}


def load_configs():
    for file in ['/etc/lhfs/lhfs.conf', './etc/lhfs.conf']:
        if not os.path.exists(file):
            continue
        CONF.load(file)
        break


CONF.register_opts(default_options)
CONF.register_opts(api_options, group='api')
CONF.register_opts(lhfs_options, group='lhfs')
CONF.register_opts(web_options, group='web')
