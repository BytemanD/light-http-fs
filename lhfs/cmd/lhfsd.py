import argparse
import logging
import os
import signal
import sys
import mimetypes
import getpass

from easy2use.globals import log

from lhfs import server
from lhfs.common import exception
from lhfs.common import conf

DEVELOPMENT = False

LOG = logging.getLogger(__name__)


def registe_stop_signal(service):

    def handle_signal(signum, frame):
        LOG.info('receive signal: %s', signum)
        service.stop()

    signal.signal(signal.SIGINT, handle_signal)
    # signal.signal(signal.SIGHUP, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)


def main():
    parser = argparse.ArgumentParser('Light HTTP FS Command')

    parser.add_argument('root', nargs='?',
                        help="the root path of FS")

    parser.add_argument('--password',
                        help="the password for admin")
    parser.add_argument('--slave', action='store_true',
                        help="run as slave mode")
    parser.add_argument('--ssh-user', default=getpass.getuser(),
                        help="ssh user")
    parser.add_argument('--ssh-password', help="ssh password")

    parser.add_argument('--theme',
                        choices=['material', 'bootstrap'],
                        help="Theme for webui")

    args = parser.parse_args()

    # NOTE(fjboy) For windows host, MIME type of js file be
    # 'text/plain', so add this type before start http server.
    mimetypes.add_type('application/javascript', '.js')

    conf.load_configs()
    CONF = conf.CONF

    if args.debug:
        CONF.set_cli('debug', args.debug)
    if args.root:
        CONF.set_cli('root', args.root, group='lhfs')

    log_configs = {}
    if CONF.debug:
        log_configs['level'] = logging.DEBUG
    if CONF.log_file:
        log_configs['filename'] = CONF.log_file

    log.basic_config(**log_configs)

    if args.root and not os.path.exists(args.root):
        raise exception.InvalidRootPath(root=args.root, reason='not exists')

    from gevent import monkey
    monkey.patch_all()

    if args.slave:
        service = server.LightHttpFSSlave(fs_root=CONF.lhfs.root,
                                          ssh_user=args.ssh_user,
                                          ssh_password=args.ssh_password)
        registe_stop_signal(service)
        service.start()
    else:
        service = server.LightHttpFS(fs_root=CONF.lhfs.root,
                                     port=CONF.lhfs.wsgi_port,
                                     password=args.password,
                                     theme=args.theme)
        service.start(develop=DEVELOPMENT)
        if not DEVELOPMENT:
            registe_stop_signal(service)


if __name__ == '__main__':
    DEVELOPMENT = True
    sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.pardir)))
    sys.exit(main())
