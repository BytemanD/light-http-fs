import enum


class Unit(enum.Enum):
    KB = 1024
    MB = KB * 1024
    GB = MB * 1024


MASTER = 'master'
SLAVE = 'slave'

RPC_CLASS_MAPPING = {
    'xmlrpc': ('lhfs.core.rpc.impl.xml.XMLRpcServer',
               'lhfs.core.rpc.impl.xml.XMLRpcClient'),
    'zerorpc': ('lhfs.core.rpc.impl.zero.ZeroRpcServer',
                'lhfs.core.rpc.impl.zero.ZeroRpcClient')
}

FOLDER = 'folder'
FILE = 'file'

ACTIVE = 'active'
DOWN = 'down'
