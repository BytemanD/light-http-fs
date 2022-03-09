import os
import sys
import bs4

import prettytable

from easy2use.common import cliparser
from easy2use.common import log
from easy2use.common import colorstr
from easy2use import date

import eventlet

eventlet.monkey_patch()


CONF = None
LOG = log.getLogger(__name__)


def parse_hearbeat(hearbeat):
    return date.parse_timestamp2str(hearbeat,
                                    date.FORMAT_YYYY_MM_DD_HHMMSS)


def colored_status(status):
    if status.lower() in ['active', 'ok', 'true', 'success', 'on']:
        return colorstr.GreenStr(status)
    return colorstr.RedStr(status)


def print_error(message):
    print(colorstr.RedStr('ERROR: ') + message)


class NodeLists(cliparser.CliBase):
    NAME = 'node-list'
    ARGUMENTS = [
        cliparser.Argument('-l', '--long', action='store_true',
                           help='show more message')
    ]

    def __call__(self, args):
        from lhfs.common import utils
        rpc_client = utils.get_rpc_client(CONF.lhfs.master_rpc)
        rows = ['hostname', 'type', 'transport', 'status', 'heartbeat']
        if args.long:
            rows.extend(['ip', 'ssh_user', 'ssh_password'])
        pt = prettytable.PrettyTable(rows)
        for node in rpc_client.list_nodes():
            LOG.debug('node: %s', node)
            row_values = [node.hostname, node.type, node.transport,
                          colored_status(node.status),
                          parse_hearbeat(node.heartbeat)]
            pt.add_row(row_values)
        print(pt)


class Ls(cliparser.CliBase):
    NAME = 'ls'
    ARGUMENTS = [
        cliparser.Argument('host'),
        cliparser.Argument('path', default='/'),
    ]

    def __call__(self, args):
        from lhfs.common import exception
        from lhfs.common import utils

        try:
            rpc_master = utils.get_rpc_client(CONF.lhfs.master_rpc)
            node = rpc_master.get_node(args.host)
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


class Du(cliparser.CliBase):
    NAME = 'du'
    ARGUMENTS = [
        cliparser.Argument('--host')
    ]

    def __call__(self, args):
        from lhfs.common import utils
        from lhfs.common import exception
        from lhfs.common import constants
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


class CollectStatic(cliparser.CliBase):
    NAME = 'collect-static'
    ARGUMENTS = [
        cliparser.Argument('file'),
        cliparser.Argument('-s', '--save', default='./'),
        cliparser.Argument('-w', '--worker', type=int, default=1),
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
                static_files.append(src)
                static_files.append(src + '.map')

            for link in html.find_all(name='link'):
                href = link.get('href')
                if not (href.startswith('http') and href.endswith('css')):
                    continue
                LOG.debug('find stylesheet: %s', href)
                static_files.append(href)
                static_files.append(href + '.map')

            from easy2use.downloader.urllib import driver
            downloader = driver.Urllib3Driver(progress=True,
                                              download_dir=args.save,
                                              keep_full_path=True,
                                              workers=args.worker)
            downloader.download_urls(static_files)


def main():
    global CONF

    from lhfs.common import conf                              # noqa

    conf.load_configs()
    CONF = conf.CONF
    cli_parser = cliparser.SubCliParser('Light Http FileSystem Client')
    cli_parser.register_clis(NodeLists, Ls, Du, CollectStatic)
    cli_parser.call()


if __name__ == '__main__':
    sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.pardir)))
    sys.exit(main())
