import argparse
import argcomplete

from media_management_scripts.commands import *

COMMANDS = {k.name: k for k in [x() for x in SubCommand.__subclasses__()]}


def build_argparse():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='Sub commands', dest='command')

    for cmd in COMMANDS.values():
        cmd.build_argparse(subparsers)
    argcomplete.autocomplete(parser)
    return parser


def main():
    parser = build_argparse()
    ns = vars(parser.parse_args())
    if ns.get('print_args', False):
        print(ns)
    cmd = ns.get('command', None)
    if not cmd or cmd not in COMMANDS:
        parser.print_usage()
    else:
        COMMANDS[cmd].execute(ns)


if __name__ == '__main__':
    main()
