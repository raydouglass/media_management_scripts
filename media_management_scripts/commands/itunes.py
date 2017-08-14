from . import SubCommand
from .common import *


class ItunesCommand(SubCommand):
    @property
    def name(self):
        return 'itunes'

    def build_argparse(self, subparser):
        itunes_parser = subparser.add_parser('itunes', parents=[parent_parser])
        itunes_parser.add_argument('-o', '--output', type=str, default='./')
        itunes_parser.add_argument('--meta-shelve', type=str, default=None, dest='meta_shelve')
        itunes_parser.add_argument('input', nargs='+', help='Input files')
        itunes_parser.add_argument('--dvd', action='store_const', default=False, const=True)
        itunes_parser.add_argument('--fuzzy', action='store_const', default=False, const=True)

    def subexecute(self, ns):
        from media_management_scripts.itunes import process_itunes_tv
        from media_management_scripts.tvdb_api import from_config
        import os
        input_to_cmd = ns['input']
        tvdb = from_config(os.path.expanduser('~/.config/tvdb/tvdb.ini'))
        output = ns['output']
        dvd = ns['dvd']
        fuzzy = ns['fuzzy']
        meta_shelve = ns['meta_shelve']
        dry_run = ns['dry_run']
        if meta_shelve:
            import shelve
            with shelve.open(meta_shelve) as meta_store:
                process_itunes_tv(input_to_cmd, output, tvdb, meta_shelve=meta_store, use_dvd=dvd, fuzzy=fuzzy,
                                  dry_run=dry_run)
        else:
            process_itunes_tv(input_to_cmd, output, tvdb, meta_shelve=None, use_dvd=dvd, fuzzy=fuzzy, dry_run=dry_run)


SubCommand.register(ItunesCommand)
