MASTER = 'master'
SLAVE = 'slave'

RPC_CLASS_MAPPING = {
    'xmlrpc': ('lhfs.rpc.impl.xml.XMLRpcServer',
               'lhfs.rpc.impl.xml.XMLRpcClient'),
    'zerorpc': ('lhfs.rpc.impl.zero.ZeroRpcServer',
                'lhfs.rpc.impl.zero.ZeroRpcClient')
}

