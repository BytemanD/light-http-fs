import argparse
import logging
import os
import sys
import mimetypes
import getpass
from easy2use.common import log

DEVELOPMENT = False


def main():
    parser = argparse.ArgumentParser('Light HTTP FS Command')
    parser.add_argument('root', nargs='?',
                        help="the root path of FS")
    parser.add_argument('-d', '--debug', action='store_true',
                        help="show debug message")
    parser.add_argument('--password',
                        help="the password for admin")
    parser.add_argument('--slave', action='store_true',
                        help="run as slave mode")
    parser.add_argument('--ssh-user', default=getpass.getuser(),
                        help="ssh user")
    parser.add_argument('--ssh-password', help="ssh password")

    args = parser.parse_args()

    # NOTE(fjboy) For windows host, MIME type of js file be
    # 'text/plain', so add this type before start http server.
    mimetypes.add_type('application/javascript', '.js')

    from lhfs import server                                   # noqa
    from lhfs.common import exception                         # noqa
    from lhfs.common import conf                              # noqa

    conf.load_configs()
    CONF = conf.CONF

    if args.debug:
        CONF.set_cli('debug', args.debug)
    if args.root:
        CONF.set_cli('root', args.root, group=CONF.lhfs.name)

    if CONF.debug:
        log.set_default(level=logging.DEBUG)

    if args.root and not os.path.exists(args.root):
        raise exception.InvalidRootPath(root=args.root, reason='not exists')

    from gevent import monkey
    monkey.patch_all()

    if args.slave:
        service = server.LightHttpFSSlave(fs_root=CONF.lhfs.root,
                                          ssh_user=args.ssh_user,
                                          ssh_password=args.ssh_password)
        service.start()
    else:
        fs_server = server.LightHttpFS(fs_root=CONF.lhfs.root,
                                       port=CONF.lhfs.wsgi_port,
                                       password=args.password)
        fs_server.start(develoment=DEVELOPMENT)


if __name__ == '__main__':
    DEVELOPMENT = True
    sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.pardir)))
    sys.exit(main())
