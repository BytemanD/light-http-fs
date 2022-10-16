import os

from tornado import ioloop
from tornado import httpserver
from tornado import web

# import flask
# from flask import session
from werkzeug.routing import BaseConverter

import logging
# from easy2use.server import httpserver

from lhfs import views
from lhfs.common import conf
from lhfs.core import manager

LOG = logging.getLogger(__name__)

CONF = conf.CONF
ROOT = os.path.dirname(os.path.abspath(__file__))


class RegexConverter(BaseConverter):

    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


class LightHttpFS(object):

    RULES = [
        (r'/', views.HomeView),
        # (r'/favicon.ico', views.FaviconView('favicon')),
        (r'/auth', views.AuthView),
        (r'/index.html', views.IndexView),
        (r'/v1/file/(?P<node>[^/]+)(?P<dir_path>.*)', views.FileViewV1),
        (r'/v1/fs/(?P<node>[^/]+)(?P<dir_path>.*)', views.FSViewV1),
        (r'/v1/search/<node>', views.SearchViewV1),
        (r'/nodes', views.NodesView),
        (r'/nodes/<hostname>', views.NodeView),
        (r'/action', views.FsActionView),
    ]

    def __init__(self, host=None, port=80, fs_root=None, password=None,):
        if password:
            LOG.info('auth request before request')
        LOG.info('use theme %s', CONF.web.theme)
        self.template_folder = os.path.join(ROOT, 'templates', CONF.web.theme)
        self.static_folder = os.path.join(ROOT, 'static')
        # self.before_request = self.auth_all_request
        # super(LightHttpFS, self).__init__(
        #     'lhfs', host=host or CONF.lhfs.wsgi_host, port=port,
        #     template_folder=os.path.join(ROOT, 'templates',
        #                                  theme or 'bootstrap'),
        #     ,
        #     converters_ext=[('regex', RegexConverter)],
        #     secret_key='lhfs-server-secret-key')

        LOG.debug('static_folder=%s, template_path=%s',
                  self.static_folder, self.template_folder)
        self.fs_root = fs_root or '.'
        # self.app.config['admin_password'] = password
        views.set_fs_manager(self.fs_root, node_type='master')
        views.set_auth_manager(password)

    # def auth_all_request(self):
    #     if flask.request.path.startswith('/static') or \
    #        flask.request.path.startswith('/login') or \
    #        flask.request.path.startswith('/auth'):
    #         return
    #     LOG.debug('session username is %s', session.get('username'))
    #     if not session.get('username'):
    #         return flask.render_template('login.html')

    def start(self, develop=False, host=None, port=None):
        from gevent import monkey
        monkey.patch_all()

        views.NODE_MANAGER.heartbeat()
        views.NODE_MANAGER.start_rpc()

        app = web.Application(self.RULES, debug=develop,
                              template_path=self.template_folder,
                              static_path=self.static_folder)

        if develop:
            app.listen(port or CONF.port, address=host)
        else:
            server = httpserver.HTTPServer(app)
            server.bind(port or CONF.port)
            server.start(num_processes=CONF.workers)

        ioloop.IOLoop.instance().start()

    def stop(self):
        views.NODE_MANAGER.stop_rpc()


class LightHttpFSSlave(object):

    def __init__(self, fs_root=None, **kwargs):
        self.manager = manager.SlaveManager(fs_root or '.', **kwargs)

    def start(self):
        self.manager.heartbeat()
        self.manager.start_rpc()

    def stop(self):
        self.manager.stop_rpc()
