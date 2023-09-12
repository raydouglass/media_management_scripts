import argparse
import argcomplete
import sys

from media_management_scripts.commands import *
from media_management_scripts import __version__ as version

COMMANDS = {k.name: k for k in [x() for x in SubCommand.__subclasses__()]}


class ArgParseException(Exception):
    def __init__(self, status):
        self.status = status


class NoExitArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super(NoExitArgumentParser, self).__init__(*args, **kwargs)

    def exit(self, status=0, message=None):
        if message:
            self._print_message(message, sys.stderr)
        raise ArgParseException(status)


def build_argparse():
    parser = NoExitArgumentParser()
    parser.add_argument(
        "-v",
        "--version",
        help="Display version",
        action="store_const",
        const=True,
        default=False,
    )
    subparsers = parser.add_subparsers(help="Sub commands", dest="command")

    for cmd in COMMANDS.values():
        cmd.build_argparse(subparsers)
    argcomplete.autocomplete(parser)
    return parser


def main():
    parser = build_argparse()
    try:
        ns = vars(parser.parse_args())
        if ns.get("version"):
            print("{} v{}".format(parser.prog, version))
        elif ns.get("print_args", False):
            print(ns)
        else:
            cmd = ns.get("command", None)
            if not cmd or cmd not in COMMANDS:
                parser.print_usage()
            else:
                COMMANDS[cmd].execute(ns)
    except ArgParseException as e:
        sys.exit(e.status)


if __name__ == "__main__":
    main()
