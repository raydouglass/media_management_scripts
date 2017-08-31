import argparse
import argcomplete

from media_management_scripts.commands import *
from media_management_scripts import version

COMMANDS = {k.name: k for k in [x() for x in SubCommand.__subclasses__()]}


def build_argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', help='Display version', action='store_const', const=True, default=False)
    subparsers = parser.add_subparsers(help='Sub commands', dest='command')

    for cmd in COMMANDS.values():
        cmd.build_argparse(subparsers)
    argcomplete.autocomplete(parser)
    return parser


def main():
    parser = build_argparse()
    ns = vars(parser.parse_args())
    if ns.get('version'):
        print('{} v{}'.format(parser.prog, version))
    elif ns.get('print_args', False):
        print(ns)
    else:
        cmd = ns.get('command', None)
        if not cmd or cmd not in COMMANDS:
            parser.print_usage()
        else:
            COMMANDS[cmd].execute(ns)


if __name__ == '__main__':
    main()
