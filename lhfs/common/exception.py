from easy2use.common import exceptions


class InvalidRootPath(exceptions.BaseException):
    _msg = 'Invalid root path: {root}, reason: {reason}'


class FileExists(exceptions.BaseException):
    _msg = 'File {path} already exists'


class FileNotExists(exceptions.BaseException):
    _msg = 'File {path} is not exists'


class NodeNotExists(exceptions.BaseException):
    _msg = 'Node {node} not exists'


class NodeInactive(exceptions.BaseException):
    _msg = 'Node {node} is inactive'
