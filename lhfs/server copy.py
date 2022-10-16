import os
import logging
import signal

from tornado import ioloop
from tornado import httpserver
from tornado import web

from lhfs import views
from lhfs.common import conf

LOG = logging.getLogger('tornado.application')

CONF = conf.CONF
ROOT = os.path.dirname(os.path.abspath(__file__))
ROUTES = [
    (r'/', views.Index),
    (r'/dashboard', views.Dashboard),
    (r'/welcome', views.Welcome),
    (r'/configs', views.Configs),
    (r'/cluster', views.Cluster),
    (r'/cluster/(.*)', views.Cluster),
    (r'/tasks', views.Tasks),
    (r'/tasks/(.*)', views.Tasks),
    (r'/identity(.*)', views.KeystoneProxy),
    (r'/computing(.*)', views.NovaProxy),
    (r'/image(.*)', views.GlanceProxy),
    (r'/networking(.*)', views.NeutronProxy),
    (r'/volume(.*)', views.CinderProxy),
    (r'/auth_info', views.AuthInfo),
]


def stop_ioloop(signum, frame):
    LOG.info('catch signal %s, stop ioloop', signum)

    ioloop.IOLoop.instance().add_callback_from_signal(
        lambda: ioloop.IOLoop.instance().stop()
    )


def start(develop=False, host=None, port=None):
    template_path = os.path.join(ROOT, 'templates')
    static_path = os.path.join(ROOT, 'static')
    app = web.Application(ROUTES, debug=develop, template_path=template_path,
                          static_path=static_path)

    LOG.info('Staring server ...')


    signal.signal(signal.SIGINT, stop_ioloop)
    signal.signal(signal.SIGTERM, stop_ioloop)

    if develop:
        app.listen(port or CONF.port, address=host)
    else:
        MAX_BODY_SIZE = 1024 * 1024 * 1024
        server = httpserver.HTTPServer(app, max_body_size=MAX_BODY_SIZE)
        server.bind(port or CONF.port)
        server.start(num_processes=CONF.workers)

    ioloop.IOLoop.instance().start()
