import copy
import functools
import json
import os
import logging

from pbr import version
from tornado import web

from easy2use.pysshpass import ssh

from lhfs import auth
from lhfs.core import manager
from lhfs.common import utils
from lhfs.common import conf

CONF = conf.CONF
LOG = logging.getLogger(__name__)

NODE_MANAGER = None
AUTH_CONTROLLER = None
SERVER_NAME = 'lhfs'
DEFAULT_CONTEXT = {
    'name': SERVER_NAME,
    'version': version.VersionInfo('lhfs').release_string()
}
CDN = {
    'bootcdn': 'https://cdn.bootcdn.net',
    'jsdelivr': 'https://cdn.jsdelivr.net'
}


def ensure_node_exists(func):

    @functools.wraps(func)
    def wrapper(self, node, *args, **kwargs):
        if node not in NODE_MANAGER.nodes:
            self.set_status(404)
            self.finish({'error': f'node {node} not exists'})
        return func(self, node, *args, **kwargs)

    return wrapper


def set_fs_manager(root_path, node_type='master'):
    global NODE_MANAGER
    if not NODE_MANAGER:
        if node_type == 'master':
            NODE_MANAGER = manager.MasterManager(root_path)
        elif node_type == 'slaver':
            NODE_MANAGER = manager.FSManager(root_path)


def set_auth_manager(password):
    global AUTH_CONTROLLER
    if not AUTH_CONTROLLER:
        AUTH_CONTROLLER = auth.AuthManager(password)


class BaseHandler(web.RequestHandler):

    def _finish_with(self, status, data=None):
        self.set_status(status)
        self.finish(data)

    def get_context(self):
        context = copy.deepcopy(DEFAULT_CONTEXT)
        context.update({'username': self.get_cookie('username', 'guest')})
        return context

    def get_resp_context(self):
        context = copy.deepcopy(DEFAULT_CONTEXT)
        context.update({'username': self.get_cookie('username', 'guest')})
        cdn = CONF.web.use_static_cdn and CDN or \
            {k: '/static/cdn' for k in CDN}
        context.update({'cdn': cdn})
        return context


class HomeView(web.RequestHandler):

    def get(self):
        self.redirect('/index.html')


class IndexView(BaseHandler):

    def get(self):
        self.render('index.html', **self.get_resp_context())


class FSViewV1(BaseHandler):

    @ensure_node_exists
    def get(self, node, dir_path):
        self.request.query
        show_all = self.get_query_argument('showAll',
                                           'false').lower() == 'true'
        sort = self.get_query_argument('sort', 'false') == 'true'
        try:
            items = NODE_MANAGER.ls(dir_path, show_all=show_all, host=node)
            if sort:
                items.sort(key=lambda i: (i.folder, i.name), reverse=True)
            usage = NODE_MANAGER.disk_usage()
            data = {'path': dir_path,
                    'children': [item.to_dict(human=True) for item in items],
                    'disk_usage': {'total': usage.total, 'used': usage.used}}
            self._finish_with(200, {'dir': data})
        except Exception as e:
            LOG.exception(e)
            self._finish_with(400, {'error': str(e)})

    @ensure_node_exists
    def delete(self, node, dir_path):
        force = self.get_query_argument('force', 'false').lower() == 'true'
        try:
            NODE_MANAGER.rm(dir_path, force=force, host=node)
            self._finish_with(204)
        except Exception as e:
            LOG.exception(e)
            self._finish_with(400, {'error': str(e)})

    @ensure_node_exists
    def post(self, node, dir_path):
        """Create dir
        POST /fs/foo/bar
        """
        try:
            NODE_MANAGER.mkdir(dir_path, host=node)
            self._finish_with(201, {'result': 'create success'})
        except Exception as e:
            LOG.exception(e)
            self._finish_with(400, {'error': str(e)})

    @ensure_node_exists
    def put(self, node, dir_path):
        """Rename file/directory
        PUT /fs/foo/bar -d '{"dir": {"new_name": "bar2"}}'
        """
        data = json.loads(self.request.body)
        new_name = data.get('dir', {}).get('new_name')
        if not new_name:
            self._finish_with(400, {'error': 'new name is none'})
            return
        try:
            NODE_MANAGER.rename(dir_path, new_name, host=node)
            self._finish_with(200, {'result': 'rename success'})
        except Exception as e:
            LOG.exception(e)
            self._finish_with(400, {'error': str(e)})


class FileViewV1(BaseHandler):

    @ensure_node_exists
    def get(self, node, dir_path):
        LOG.info('get file from %s %s', node, dir_path)
        abs_path = NODE_MANAGER.get_abs_path(dir_path, host=node)
        if node == NODE_MANAGER.node.hostname:
            if not NODE_MANAGER.is_file(dir_path):
                self._finish_with(400, {'error': 'path is not a file'})
                return
            directory = os.path.dirname(abs_path)
            send_file = os.path.basename(abs_path)
            with open(os.path.join(directory, send_file), 'rb') as f:
                while True:
                    data = f.read(1024 * 10)
                    if not data:
                        break
                    self.write(data)
        else:
            node_info = NODE_MANAGER.nodes.get(node)
            file_size = NODE_MANAGER.file_size(dir_path, host=node)
            self.set_header('content-length', file_size)
            for data in utils.stream_generator(node_info, abs_path):
                self.write(data)
        self.set_status(200)
        self.finish()

    @ensure_node_exists
    def post(self, node, dir_path):
        f = self.request.files.get('file')
        if not f:
            self._finish_with(401, {'error': 'file is null'})
            return
        if node == NODE_MANAGER.node.hostname:
            NODE_MANAGER.save_file(dir_path, f)
        else:
            node_info = NODE_MANAGER.nodes.get(node)
            sshclient = ssh.SSHClient(node_info['ip'], node_info['ssh_user'],
                                      node_info['ssh_password'])
            save_path = f'{dir_path}/{f.filename}'
            abs_path = NODE_MANAGER.get_abs_path(save_path, host=node)
            NODE_MANAGER.ensure_parent_dir(save_path, host=node)
            sshclient.putfo(f, abs_path, f.content_length)
        self._finish_with(200, {'files': {'result': 'file save success'}})


class SearchViewV1(BaseHandler):

    def get(self, node):
        self._finish_with(
            200,
            {'search': {'history': NODE_MANAGER.get_search_history(host=node)}}
        )

    @ensure_node_exists
    def post(self, node):
        """
        params: {'search': {'partern': '*.py'}}
        """
        data = json.loads(self.request.body)
        partern = data.get('search', {}).get('partern')
        if not partern:
            self._finish_with(400, {'error': 'partern is none'})
            return
        matched_pathes = NODE_MANAGER.find(partern, host=node)
        self._finish_with(200, {'search': {'dirs': matched_pathes}})


class AuthView(BaseHandler):

    def post(self):
        data = self.request.body
        if not data:
            self._finish_with(400, {'error': 'auth info not found'})
            return
        auth = json.loads(data).get('auth', {})
        LOG.debug('auth with: %s', auth)
        if not AUTH_CONTROLLER.is_valid(auth.get('username'),
                                        auth.get('password')):
            self.set_cookie('username', auth.get('username'))
            return
        self._finish_with(204)

    def delete(self):
        self.clear_all_cookies()
        self._finish_with(204)
        return


class NodesView(BaseHandler):

    def get(self):
        nodes = NODE_MANAGER.list_nodes()
        self._finish_with(200, {'nodes': [node.to_dict() for node in nodes]})


class NodeView(web.RequestHandler):

    def get(self, hostname):
        node = NODE_MANAGER.get_node(hostname)
        return {'node': node.to_dict()}


class FsActionView(BaseHandler):

    ACTION_MAPPING = {
        'doZip': 'do_zip',
        'doUnzip': 'do_unzip',
    }

    def post(self):
        data = json.loads(self.request.body)
        action_name = list(data.keys())[0]
        if action_name not in self.ACTION_MAPPING:
            self._finish_with(400, {'error': f'Invalid action {action_name}'})
            return
        return getattr(self, self.ACTION_MAPPING[action_name])(data)

    def do_zip(self, data):
        path = data.get('doZip', {}).get('path')
        if not path:
            self._finish_with(400, {'error': 'path is none'})
            return
        zip_name = NODE_MANAGER.zip_path(path)
        LOG.debug('zip name is : %s', zip_name)
        self._finish_with(200, {'message': f'zip {zip_name} success'})
        return

    def do_unzip(self, data):
        params = data.get('doUnzip')
        path = params.get('path')
        if not path:
            return {'error': 'path is none'}, 400
        path = params.get('path')
        zip_name = NODE_MANAGER.unzip_path(path)
        LOG.debug('zip name is : %s', zip_name)
        return {'message': 'unzip{} success'.format(zip_name)}
