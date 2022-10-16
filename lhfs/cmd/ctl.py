import getpass
import logging
import mimetypes
import os
import sys

import bs4
import prettytable

from easy2use.common import colorstr
from easy2use.globals import cli
from easy2use.globals import log
from easy2use import date
from easy2use import system

from lhfs.common import conf
from lhfs.common import exception
from lhfs.common import utils
from lhfs.common import constants

from lhfs import server

CONF = None
LOG = logging.getLogger(__name__)


def parse_hearbeat(hearbeat):
    return date.parse_timestamp2str(hearbeat, date.YMD_HMS)


def colored_status(status):
    if status.lower() in ['active', 'ok', 'true', 'success', 'on']:
        return colorstr.GreenStr(status)
    return colorstr.RedStr(status)


def print_error(message):
    print(colorstr.RedStr('ERROR: ') + message)


class NodeLists(cli.SubCli):
    NAME = 'node-list'
    ARGUMENTS = log.get_args() + [
        cli.Arg('-m', '--master', default='http://localhost:9527',
                help='Master rpc address'),
        cli.Arg('-l', '--long', action='store_true', help='show more message'),
    ]

    def __call__(self, args):
        LOG.debug('master rpc address %s', args.master)
        rpc_client = utils.get_rpc_client(args.master)
        rows = ['hostname', 'type', 'transport', 'status', 'heartbeat']
        if args.long:
            rows.extend(['ip', 'ssh_user', 'ssh_password'])
        pt = prettytable.PrettyTable(rows)
        nodes = rpc_client.list_nodes()
        LOG.debug('get nodes: %s', nodes)
        for node in nodes:
            row_values = [node.hostname, node.type, node.transport,
                          colored_status(node.status),
                          parse_hearbeat(node.heartbeat)]
            pt.add_row(row_values)
        print(pt)


class Ls(cli.SubCli):
    NAME = 'ls'
    ARGUMENTS = log.get_args() + [
        cli.Arg('--host', help='The host to list, default is master host'),
        cli.Arg('-m', '--master', default='http://localhost:9527',
                help='Master rpc address'),
        cli.Arg('path', nargs='?', default='/', help='default path: /'),
    ]

    def __call__(self, args):
        try:
            rpc_master = utils.get_rpc_client(args.master)
            node = rpc_master.get_node(args.host) if args.host \
                else rpc_master.get_master_nodes()
            if not node:
                raise exception.NodeNotExists(node=args.host)
        except exception.NodeNotExists as e:
            print_error(e)
            return 1

        rpc_client = utils.get_rpc_client(node.transport)
        line = '{} {:30} {:>10} {}'
        try:
            for item in rpc_client.ls(args.path):
                item_dict = item.to_dict(human=True)
                print(line.format(item.folder and 'd' or '-',
                                  item.name, item_dict['size'],
                                  item_dict['mtime']))
        except Exception as e:
            LOG.error(e)


class Du(cli.SubCli):
    NAME = 'du'
    ARGUMENTS = [
        cli.Arg('--host')
    ]

    def __call__(self, args):
        try:
            rpc_master = utils.get_rpc_client(CONF.lhfs.master_rpc)
            if args.host:
                node = rpc_master.get_node(args.host)
                if not node:
                    raise exception.NodeNotExists(node=args.host)
                nodes = [node]
            else:
                nodes = rpc_master.list_nodes()
            LOG.debug('nodes: %s', nodes)
            if not nodes:
                raise exception.NodeNotExists(node=args.host)
        except exception.NodeNotExists as e:
            print_error(e)
            return 1

        rows = ['hostname', 'total', 'used', 'percent']
        pt = prettytable.PrettyTable(rows)
        for node in nodes:
            if node.status != constants.ACTIVE:
                LOG.warning('Node %s is inactive, skip.', node.hostname)
                pt.add_row([node.hostname, '-', '-', '-'])
                continue
            rpc_client = utils.get_rpc_client(node.transport)
            usage = rpc_client.disk_usage().to_dict(human=True)
            pt.add_row([node.hostname, usage.get('total'), usage.get('used'),
                        usage.get('percent')])
        print(pt)


class CollectStatic(cli.SubCli):
    NAME = 'collect-static'
    ARGUMENTS = [
        cli.Arg('file'),
        cli.Arg('-s', '--save', default='./'),
        cli.Arg('-w', '--worker', type=int, default=1),
    ]

    def __call__(self, args):
        with open(args.file) as f:
            html = bs4.BeautifulSoup(f.read(), features="html.parser")
        static_files = []
        for script in html.find_all(name='script'):
            src = script.get('src')
            if not (src.startswith('http') and src.endswith('.js')):
                continue
            LOG.debug('find javascript: %s', src)
            static_files.extend((src, f'{src}.map'))
        for link in html.find_all(name='link'):
            href = link.get('href')
            if not (href.startswith('http') and href.endswith('css')):
                continue
            LOG.debug('find stylesheet: %s', href)
            static_files.extend((href, f'{href}.map'))
        # from easy2use.downloader.urllib import driver
        # downloader = driver.Urllib3Driver(progress=True,
        #                                   download_dir=args.save,
        #                                   keep_full_path=True,
        #                                   workers=args.worker)
        # downloader.download_urls(static_files)
        import requests
        session = requests.Session()
        for url in static_files:
            LOG.info('download %s', url)
            try:
                session.get(static_files[0], verify='cacert.pem')
            except Exception as e:
                LOG.error(e)
                break


class Serve(cli.SubCli):
    NAME = 'serve'
    ARGUMENTS = log.get_args() + [
        cli.Arg('root', nargs='?', help="the root path of FS"),
        cli.Arg('--password', help="the password for admin"),
        cli.Arg('--slave', action='store_true', help="run as slave mode"),
        cli.Arg('--ssh-user', default=getpass.getuser(), help="ssh user"),
        cli.Arg('--ssh-password', help="ssh password"),
        cli.Arg('--develop', action='store_true'),
    ]

    def __call__(self, args):
        if system.OS.is_windows():
            # NOTE(fjboy) For windows host, MIME type of .js file is
            # 'text/plain', so add this type before start http server.
            mimetypes.add_type('application/javascript', '.js')

        LOG.debug('load configs')
        LOG.info('load configs')
        conf.load_configs()

        if args.slave:
            service = server.LightHttpFSSlave(fs_root=CONF.lhfs.root,
                                              ssh_user=args.ssh_user,
                                              ssh_password=args.ssh_password)
            service.start()
        else:
            service = server.LightHttpFS(fs_root=CONF.lhfs.root,
                                         password=args.password)
            service.start(develop=args.develop)


def main():
    global CONF

    conf.load_configs()
    CONF = conf.CONF

    cli_parser = cli.SubCliParser('Light Http FileSystem Client',
                                  title='SubCommands')
    cli_parser.register_clis(NodeLists, Ls, Du, CollectStatic, Serve)
    cli_parser.call()


if __name__ == '__main__':
    sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.pardir)))
    sys.exit(main())
