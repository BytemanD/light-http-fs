import copy
import flask
import functools
import json
import os

from flask import views
from flask import current_app
from flask.globals import session

from easy2use.common import log
from easy2use.common import utils as e2u_utils
from easy2use.pysshpass import ssh

from lhfs import auth
from lhfs.fs import manager
from lhfs.common import utils
from lhfs.common import conf

CONF = conf.CONF
LOG = log.getLogger(__name__)

NODE_MANAGER = None
AUTH_CONTROLLER = None
SERVER_NAME = 'lhfs'
DEFAULT_CONTEXT = {
    'name': SERVER_NAME,
    'version': e2u_utils.package_version('lhfs') or 'dev'
}


def ensure_node_exists(func):

    @functools.wraps(func)
    def wrapper(self, node, *args, **kwargs):
        if node not in NODE_MANAGER.nodes:
            return json_response({'error': 'node {} not exists'.format(node)},
                                 status=400)
        return func(self, node, *args, **kwargs)

    return wrapper


def json_response(data, status=200):
    return flask.Response(json.dumps(data), status=status,
                          headers={'Content-Type': 'application/json'})


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


def get_resp_context():
    context = copy.deepcopy(DEFAULT_CONTEXT)
    context.update({'username': session.get('username', 'guest')})
    context.update({
        'STATIC_URL': '/static',
        'STATIC_CDN': CONF.web.use_static_cdn and '/static/cdn' or None})
    return context


class HomeView(views.MethodView):

    def get(self):
        return flask.redirect('/index.html')


class IndexView(views.MethodView):

    def get(self):
        return flask.render_template('index.html',
                                     **get_resp_context())


class FaviconView(views.MethodView):

    def get(self):
        return flask.send_from_directory(
            os.path.join(current_app.static_folder,
                         'icon'), 'icon-black-circle.svg')


class FSViewV1(views.MethodView):

    @ensure_node_exists
    def get(self, node, dir_path):
        show_all = utils.get_reqeust_arg(flask.request, 'showAll',
                                         default=False)
        sort = utils.get_reqeust_arg(flask.request, 'sort', default=False)
        try:
            items = NODE_MANAGER.ls(dir_path, show_all=show_all, host=node)
            if sort:
                items.sort(key=lambda i: (i.folder, i.name), reverse=True)
            usage = NODE_MANAGER.disk_usage()
        except Exception as e:
            LOG.exception(e)
            return str(e), 400

        return flask.jsonify({'dir': {
            'path': dir_path,
            'children': [item.to_dict(human=True) for item in items],
            'disk_usage': {'total': usage.total, 'used': usage.used}}
        })

    @ensure_node_exists
    def delete(self, node, dir_path):
        force = utils.get_reqeust_arg(flask.request, 'force', default=False)
        try:
            NODE_MANAGER.rm(dir_path, force=force, host=node)
        except Exception as e:
            LOG.exception(e)
            return json_response({'error': str(e)}, status=400)
        return json_response({'result': 'delete success'})

    @ensure_node_exists
    def post(self, node, dir_path):
        """Create dir
        POST /fs/foo/bar
        """
        try:
            NODE_MANAGER.mkdir(dir_path, host=node)
        except Exception as e:
            LOG.exception(e)
            return json_response({'error': str(e)}, status=400)
        return json_response({'result': 'create success'})

    @ensure_node_exists
    def put(self, node, dir_path):
        """Rename file/directory
        PUT /fs/foo/bar -d '{"dir": {"new_name": "bar2"}}'
        """
        data = json.loads(flask.request.data)
        new_name = data.get('dir', {}).get('new_name')
        if not new_name:
            return json_response({'error': 'new name is none'}, status=400)
        try:
            NODE_MANAGER.rename(dir_path, new_name, host=node)
        except Exception as e:
            LOG.exception(e)
            return json_response({'error': str(e)}, status=400)
        return json_response({'result': 'rename success'})


class FileViewV1(views.MethodView):

    @ensure_node_exists
    def get(self, node, dir_path):
        LOG.debug('get file from %s %s', node, dir_path)
        abs_path = NODE_MANAGER.get_abs_path(dir_path, host=node)
        if node == NODE_MANAGER.node.hostname:
            if not NODE_MANAGER.is_file(dir_path):
                return json_response({'error': 'path is not a file'},
                                     status=400)
            directory = os.path.dirname(abs_path)
            send_file = os.path.basename(abs_path)
            return flask.send_from_directory(directory, send_file,
                                             as_attachment=False)
        else:
            node_info = NODE_MANAGER.nodes.get(node)
            file_size = NODE_MANAGER.file_size(dir_path, host=node)
            resp = flask.Response(
                flask.stream_with_context(utils.stream_generator(node_info,
                                                                 abs_path)),
                content_type="application/octet-stream")
            resp.headers['content-length'] = file_size
            return resp

    @ensure_node_exists
    def post(self, node, dir_path):
        f = flask.request.files.get('file')
        if not f:
            return json_response({'error': 'file is null'}, status=401)
        if node == NODE_MANAGER.node.hostname:
            NODE_MANAGER.save_file(dir_path, f)
        else:
            node_info = NODE_MANAGER.nodes.get(node)
            sshclient = ssh.SSHClient(node_info['ip'], node_info['ssh_user'],
                                      node_info['ssh_password'])
            save_path = '{}/{}'.format(dir_path, f.filename)
            abs_path = NODE_MANAGER.get_abs_path(save_path, host=node)
            NODE_MANAGER.ensure_parent_dir(save_path, host=node)
            sshclient.putfo(f, abs_path, f.content_length)
        return json_response({'files': {'result': 'file save success'}})


class SearchViewV1(views.MethodView):

    def get(self, node):
        return json_response({
            'search': {
                'history': NODE_MANAGER.get_search_history(host=node)}
        })

    @ensure_node_exists
    def post(self, node):
        """
        params: {'search': {'partern': '*.py'}}
        """
        data = json.loads(flask.request.data)
        partern = data.get('search', {}).get('partern')
        if not partern:
            return json_response({'error': 'partern is none'}, status=400)
        matched_pathes = NODE_MANAGER.find(partern, host=node)

        return json_response({'search': {'dirs': matched_pathes}})


class AuthView(views.MethodView):

    def post(self):
        data = flask.request.data
        if not data:
            return json_response({'error': 'auth info not found'},
                                 status=400)
        auth = json.loads(data).get('auth', {})
        LOG.debug('auth with: %s', auth)
        if AUTH_CONTROLLER.is_valid(auth.get('username'),
                                    auth.get('password')):
            session['username'] = auth.get('username')
            return json_response({}, status=200)
        else:
            return json_response({'error': 'auth failed'}, status=401)

    def delete(self):
        data = flask.request.data
        auth = json.loads(data).get('auth', {})
        LOG.debug('auth with: %s', auth)
        if 'username' in session:
            del session['username']

    def delete(self):
        session.clear()
        return json_response({}, status=204)


class NodesView(views.MethodView):

    def get(self):
        nodes = NODE_MANAGER.list_nodes()
        return {'nodes': [node.to_dict() for node in nodes]}


class NodeView(views.MethodView):

    def get(self, hostname):
        node = NODE_MANAGER.get_node(hostname)
        return {'node': node.to_dict()}


class FsActionView(views.MethodView):

    def post(self):
        data = json.loads(flask.request.data)
        action_name = list(data.keys())[0]
        # import pdb
        # pdb.set_trace()
        if action_name == 'doZip':
            self.do_zip(data.get('doZip'))
        return {action_name: {}}

    def do_zip(self, params):
        path = params.get('path')
        if not path:
            return {'error': 'path is none'}, 400

        path = params.get('path')
        zip_name = NODE_MANAGER.zip_path(path)
        LOG.debug('zip name is : %s', zip_name)
