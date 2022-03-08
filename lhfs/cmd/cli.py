import os
import sys

import prettytable

from easy2use.common import cliparser
from easy2use.common import log
from easy2use.common import colorstr
from easy2use import date


CONF = None
LOG = log.getLogger(__name__)


def parse_hearbeat(hearbeat):
    return date.parse_timestamp2str(hearbeat,
                                    date.FORMAT_YYYY_MM_DD_HHMMSS)


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
        for node in rpc_client.get_nodes(None):
            row_values = []
            for row in rows:
                value = node.get(row)
                if row == 'status':
                    value = (value == ':)' and colorstr.GreenStr(value)) or \
                        colorstr.RedStr(value)
                elif row == 'heartbeat':
                    value = parse_hearbeat(value)
                row_values.append(value)
            pt.add_row(row_values)
        print(pt)


class Ls(cliparser.CliBase):
    NAME = 'ls'
    ARGUMENTS = [
        cliparser.Argument('host'),
        cliparser.Argument('path'),
    ]

    def __call__(self, args):
        from lhfs.common import exception
        from lhfs.common import utils
        try:
            rpc_master = utils.get_rpc_client(CONF.lhfs.master_rpc)
            nodes = rpc_master.get_nodes(args.host)
            if not nodes:
                raise exception.NodeNotExists(node=args.host)
        except exception.NodeNotExists as e:
            print_error(e)
            return 1

        rpc_client = utils.get_rpc_client(nodes[0].get('transport'))
        line = '{} {:30} {:10} {}'
        for item in rpc_client.ls(args.path or '/'):
            print(line.format(item.get('type') == 'folder' and 'd' or '-',
                              item.get('name'), item.get('size'),
                              item.get('modify_time')))



class Du(cliparser.CliBase):
    NAME = 'du'
    ARGUMENTS = [
        cliparser.Argument('--host')
    ]

    def __call__(self, args):
        from lhfs.fs import manager
        from lhfs.common import utils
        from lhfs.common import exception
        try:
            rpc_master = utils.get_rpc_client(CONF.lhfs.master_rpc)
            nodes = rpc_master.get_nodes(args.host)
            if not nodes:
                raise exception.NodeNotExists(node=args.host)
        except exception.NodeNotExists as e:
            print_error(e)
            return 1

        rows = ['hostname', 'total', 'used', 'percent']
        pt = prettytable.PrettyTable(rows)
        unit = 1024 * 1024
        for node in nodes:
            if node.get('status') != ':)':
                LOG.warning('Node %s is inactive, skip.', node.get('hostname'))
                pt.add_row([node.get('hostname'), '-', '-', '-'])
                continue

            rpc_client = manager.get_rpc_client(node.get('transport'))
            usage = rpc_client.disk_usage()
            row_values = [node.get('hostname')]
            row_values.extend([
                '{:.2f}G'.format(usage.get(r) / unit) for r in rows[1:-1]])
            row_values.append('{:.2f}%'.format(usage.get(rows[-1])))
            pt.add_row(row_values)
        print(pt)


def main():
    global CONF

    from lhfs.common import conf                              # noqa

    conf.load_configs()
    CONF = conf.CONF
    cli_parser = cliparser.SubCliParser('Light Http FileSystem Client')
    cli_parser.register_clis(NodeLists, Ls, Du)
    cli_parser.call()


if __name__ == '__main__':
    sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.pardir)))
    sys.exit(main())
