import os

import flask
from flask import session
from werkzeug.routing import BaseConverter

from easy2use.common import log
from easy2use.server import httpserver

from lhfs import views
from lhfs.common import conf
from lhfs.fs import manager

CONF = conf.CONF

LOG = log.getLogger(__name__)
ROUTE = os.path.dirname(os.path.abspath(__file__))


class RegexConverter(BaseConverter):

    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


class LightHttpFS(httpserver.WsgiServer):

    RULES = [
        (r'/', views.HomeView.as_view('home')),
        (r'/favicon.ico', views.FaviconView.as_view('favicon')),
        (r'/auth', views.AuthView.as_view('auth')),
        (r'/index.html', views.IndexView.as_view('index')),
        (r'/v1/file/<node><regex("/|/.*"):dir_path>',
            views.FileViewV1.as_view('v1_file')),
        (r'/v1/fs/<node><regex("/|/.*"):dir_path>',
            views.FSViewV1.as_view('v1_fs')),
        (r'/v1/search/<node>', views.SearchViewV1.as_view('v1_search')),
        (r'/nodes', views.NodesView.as_view('nodes')),
        (r'/nodes/<hostname>', views.NodeView.as_view('node')),
        (r'/action', views.FsActionView.as_view('action')),
    ]

    def __init__(self, host=None, port=80, fs_root=None, password=None):
        if password:
            LOG.info('auth request before request')
            self.before_request = self.auth_all_request
        super(LightHttpFS, self).__init__(
            'lhfs', host=host or CONF.lhfs.wsgi_host, port=port,
            template_folder=os.path.join(ROUTE, 'templates'),
            static_folder=os.path.join(ROUTE, 'static'),
            converters_ext=[('regex', RegexConverter)],
            secret_key='lhfs-server-secret-key')
        LOG.debug('static_folder=%s, template_path=%s',
                  self.static_folder, self.template_folder)
        self.fs_root = fs_root or '.'
        self.app.config['admin_password'] = password
        views.set_fs_manager(self.fs_root, node_type='master')
        views.set_auth_manager(password)

    def start(self, develoment=False, use_reloader=False):
        views.NODE_MANAGER.heartbeat()
        views.NODE_MANAGER.start_rpc()
        return super(LightHttpFS, self).start(develoment=develoment,
                                              use_reloader=use_reloader)

    def auth_all_request(self):
        if flask.request.path.startswith('/static') or \
           flask.request.path.startswith('/login') or \
           flask.request.path.startswith('/auth'):
            return
        LOG.debug('session username is %s', session.get('username'))
        if not session.get('username'):
            return flask.render_template('login.html')


class LightHttpFSSlave(object):

    def __init__(self, fs_root=None, **kwargs):
        self.manager = manager.SlaveManager(fs_root or '.', **kwargs)

    def start(self):
        self.manager.heartbeat()
        self.manager.start_rpc()
