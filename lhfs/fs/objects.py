import os
import stat
import socket
import mimetypes
import dataclasses

from easy2use import fs

from easy2use import date
from easy2use.common import log
from lhfs.common import exception
from lhfs.common import utils

LOG = log.getLogger(__name__)


class BaseDataClass:

    @classmethod
    def from_dict(cls, dict_obj):
        return cls(**dict_obj)

    def to_dict(self, human=False):
        dict_obj = dataclasses.asdict(self)
        if human:
            for k in dict_obj:
                if not hasattr(self, f'_human_{k}'):
                    continue
                dict_obj[k] = getattr(self, f'_human_{k}')()
        return dict_obj


@dataclasses.dataclass
class DirItem:
    name: str = None
    size: int = None
    folder: bool = False
    mtime: float = None
    editable: bool = False
    type: str = None
    pardir: str = None

    def __post_init__(self):
        self.type = os.path.splitext(self.name)[1][1:]

    def _human_size(self):
        return utils.human_size(self.size)

    def _human_mtime(self):
        if not self.mtime:
            return self.mtime
        from easy2use import date
        return date.parse_timestamp2str(self.mtime, '%Y/%m/%d %H:%M')

    def to_dict(self, human=False):
        dict_obj = dataclasses.asdict(self)
        if human:
            for k in dict_obj:
                if not hasattr(self, f'_human_{k}'):
                    continue
                dict_obj[k] = getattr(self, f'_human_{k}')()
        return dict_obj

    @classmethod
    def from_dict(cls, dict_obj):
        return cls(**dict_obj)


@dataclasses.dataclass
class DiskUsageKB(BaseDataClass):
    total: int = 0
    used: int = 0
    free: int = 0
    percent: float = 0

    def _human_total(self):
        return utils.human_size(self.total * 1024)

    def _human_used(self):
        return utils.human_size(self.used * 1024)

    def _human_free(self):
        return utils.human_size(self.free * 1024)

    def _human_percent(self):
        return f'{self.percent} %'


@dataclasses.dataclass
class Node(BaseDataClass):
    type: str = None
    hostname: str = socket.gethostname()
    ip: str = socket.gethostbyname(socket.gethostname())
    transport: str = None
    ssh_user: str = None
    ssh_password: str = None
    heartbeat: str = None
    status: str = None


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
        return human and utils.human_size(pathstat.st_size) or pathstat.st_size

    def dict_info(self):
        return DirItem(os.path.basename(self.logic), self.size(),
                       self.is_dir(), self.stat().st_atime)

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
            path_dict.editable = child_lp.editable()
            dirs.append(path_dict)
        return dirs

    def save(self, fo):
        LOG.debug('fo %s', fo)
        LOG.debug('save file %s', self.abs_path())
        fo.save(self.abs_path())

    def ensure_parent_dir(self):
        parent_path = os.path.dirname(self.abs_path())
        if not os.path.exists(parent_path):
            LOG.debug('makedirs %s', parent_path)
            os.makedirs(parent_path)
