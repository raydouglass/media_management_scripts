from . import SubCommand
from .common import *


class TvRenameCommand(SubCommand):
    @property
    def name(self):
        return 'tv-rename'

    def build_argparse(self, subparser):
        tv_rename_parser = subparser.add_parser('tv-rename', help='Renames files in a directory to sXXeYY',
                                                parents=[parent_parser])
        tv_rename_parser.add_argument('-s', '--season', default=1, help='The season to use', type=int)
        tv_rename_parser.add_argument('-e', '--episode', default=1, help='The episode to start with', type=int)
        tv_rename_parser.add_argument('--show', default=None, help='The name of the show', type=str)
        tv_rename_parser.add_argument('--output', default=None, help='The output directory to move & rename to',
                                      type=str)
        tv_rename_parser.add_argument('input', nargs='*',
                                      help='The directories to search for files. These will be processed in order.')

    def subexecute(self, ns):
        from media_management_scripts.renamer import run
        input_to_cmd = ns['input']
        season = ns.get('season', 1)
        episode = ns.get('episode', 1)
        show = ns.get('show', None)
        dry_run = ns.get('dry_run', False)
        output = ns.get('output', None)
        run(input_to_cmd, season, episode, show, dry_run, output)


SubCommand.register(TvRenameCommand)
