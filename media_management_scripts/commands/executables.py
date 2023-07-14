from . import SubCommand
from .common import *
from media_management_scripts.support.executables import (
    EXECUTABLES,
    ExecutableNotFoundException,
)


class ExecutablesCommand(SubCommand):
    @property
    def name(self):
        return "executables"

    def build_argparse(self, subparser):
        split_parser = subparser.add_parser(
            "executables",
            help="Print the executables that will be used in other commands",
            parents=[parent_parser],
        )

    def _resolve_executable(self, func):
        try:
            return func()
        except ExecutableNotFoundException:
            return "Not found"

    def subexecute(self, ns):
        executables = [
            (exe.__name__, self._resolve_executable(exe)) for exe in EXECUTABLES
        ]
        self._bulk_print(executables, ["Name", "Path"])


SubCommand.register(ExecutablesCommand)
