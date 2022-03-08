import os
import stat
import mimetypes
import socket

from easy2use import fs

from easy2use import date
from easy2use.common import log
from lhfs.common import exception

LOG = log.getLogger(__name__)

ONE_KB = 1024
ONE_MB = ONE_KB * 1024
ONE_GB = ONE_MB * 1024


class LogicPath(object):

    def __init__(self, root, logic):
        self.root = root
        self.logic = self.safe_path(logic)
        self._abs_path = None
        self._stat = None

    def safe_path(self, logic_path):
        if not logic_path:
            return '.'
        if logic_path.startswith('/'):
            return logic_path[1:]
        return logic_path

    def abs_path(self):
        if not self._abs_path:
            self._abs_path = os.path.join(self.root, *self._logic_to_list())
        return self._abs_path

    def _logic_to_list(self):
        return self.logic and self.logic.split('/') or []

    def exists(self):
        return os.path.exists(self.abs_path())

    def delete(self, recursive=False):
        if not self.exists():
            raise exception.FileNotExists(path=self.logic)
        fs.remove(self.abs_path(), recursive=recursive)

    def is_dir(self):
        return stat.S_ISDIR(self.stat().st_mode)

    def stat(self):
        if not self._stat:
            self._stat = os.stat(self.abs_path())
        return self._stat

    def access(self, *args):
        return os.access(self.abs_path(), *args)

    def size(self, human=False):
        pathstat = self.stat()
        if not human:
            return pathstat.st_size
        if pathstat.st_size >= ONE_GB:
            return '{:.2f} GB'.format(pathstat.st_size / ONE_GB)
        elif pathstat.st_size >= ONE_MB:
            return '{:.2f} MB'.format(pathstat.st_size / ONE_MB)
        elif pathstat.st_size >= ONE_KB:
            return '{:.2f} KB'.format(pathstat.st_size / ONE_KB)
        else:
            return '{:.2f} B'.format(pathstat.st_size)

    def dict_info(self):
        return {
            'name': os.path.basename(self.logic),
            'size': self.size(human=True),
            'modify_time': self.modify_time(),
            'type': 'folder' if self.is_dir() else 'file',
        }

    def modify_time(self):
        pathstat = self.stat()
        return date.parse_timestamp2str(pathstat.st_mtime, '%Y/%m/%d %H:%M')

    def rename(self, new_name):
        abs_path = self.abs_path()
        new_path = os.path.join(os.path.dirname(abs_path), new_name)
        os.rename(abs_path, new_path)

    def mkdir(self):
        if self.exists():
            return FileExistsError(self.logic)
        return os.makedirs(self.abs_path())

    def file_content(self):
        if not self.exists():
            return exception.FileNotExists(path=self.logic)
        if self.is_dir():
            return ValueError('path is not a directory: %s' % self.logic)
        with open(self.abs_path(), 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return ''.join(lines)

    def guess_file_type(self):
        file_suffix_map = {
            'video': ['mp4', 'avi', 'mpeg'],
            'pdf': ['pdf'],
            'word': ['word'],
            'excel': ['xls', 'xlsx'],
            'archive': ['zip', 'tar', 'rar', '7zip'],
            'python': ['py', 'pyc']
        }
        suffix = os.path.splitext(os.path.basename(self.logic))[1]
        if suffix:
            suffix = suffix[1:].lower()
            for key, values in file_suffix_map.items():
                if suffix in values:
                    return key
        return 'file'

    def editable(self):
        abs_path = self.abs_path()
        if os.path.isfile(abs_path):
            t, _ = mimetypes.guess_type(abs_path)
            if t in ['text/plain', 'application/x-sh']:
                return True
        return False

    def name(self):
        return os.path.basename(self.logic)

    def ls(self, show_all=False):
        if not self.is_dir():
            return [self.dict_info()]
        dirs = []
        LOG.debug('ls: %s', self.abs_path())
        for child in os.listdir(self.abs_path()):
            child_path = '{}/{}'.format(self.logic, child)
            child_lp = LogicPath(self.root, child_path)
            if not show_all and child.startswith('.'):
                continue
            path_dict = child_lp.dict_info()
            path_dict['editable'] = child_lp.editable()
            dirs.append(path_dict)
        return sorted(dirs, key=lambda k: k['type'], reverse=True)

    def save(self, fo):
        LOG.debug('fo %s', fo)
        LOG.debug('save file %s', self.abs_path())
        fo.save(self.abs_path())

    def ensure_parent_dir(self):
        parent_path = os.path.dirname(self.abs_path())
        if not os.path.exists(parent_path):
            LOG.debug('makedirs %s', parent_path)
            os.makedirs(parent_path)


class Node(object):
    dict_attrs = ['hostname', 'type', 'transport', 'ip',
                  'ssh_user', 'ssh_password',]

    def __init__(self, node_type, hostname=None, transport=None,
                 ip=None, ssh_user='root', ssh_password=None):
        self.hostname = hostname or socket.gethostname()
        self.type = node_type
        self.transport = transport
        self.ip = ip or socket.gethostbyname(self.hostname)
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password

    def to_dict(self):
        return {attr: getattr(self, attr) for attr in self.dict_attrs}


class DiskUsage(object):
    dict_attrs = ['total', 'used', 'free', 'percent']

    def __init__(self, usage):
        self._usage = usage

    def to_dict(self):
        data = {attr: getattr(
            self._usage, attr) / 1024 for attr in self.dict_attrs[:-1]}
        data[self.dict_attrs[-1]] = getattr(self._usage, self.dict_attrs[-1])
        return data
