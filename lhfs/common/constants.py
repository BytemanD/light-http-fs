import enum


class Unit(enum.Enum):
    KB = 1024
    MB = KB * 1024
    GB = MB * 1024


MASTER = 'master'
SLAVE = 'slave'

RPC_CLASS_MAPPING = {
    'xmlrpc': ('lhfs.rpc.impl.xml.XMLRpcServer',
               'lhfs.rpc.impl.xml.XMLRpcClient'),
    'zerorpc': ('lhfs.rpc.impl.zero.ZeroRpcServer',
                'lhfs.rpc.impl.zero.ZeroRpcClient')
}

FOLDER = 'folder'
FILE = 'file'

ACTIVE = 'active'
DOWN = 'down'
