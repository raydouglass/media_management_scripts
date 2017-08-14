from . import SubCommand
from .common import *


class RenameCommand(SubCommand):
    @property
    def name(self):
        return 'rename'

    def build_argparse(self, subparser):
        import argparse
        rename_parser = subparser.add_parser('rename', parents=[parent_parser],
                                             help="Renames a set of files to the specified template",
                                             formatter_class=argparse.RawTextHelpFormatter,
                                             description="""
        Rename files based on a template.

        Templates can include variables or expressions by surrounding with ${...}. Functions can be called like ${upper(i)} or ${i | upper}.

        The following variables are available:
            * i/index - The index of the current file being renamed
            * ext - The file extension of the current file
            * filename - The filename of the current file (basename)
            * re/regex - A list of regex match groups (use re[0], re[1], etc)

        The following functions are available:
            * upper - Upper cases the input
            * lower - Lower cases the input
            * ifempty(a, b) - If a is not null, then a, otherwise b
            * lpad(a, b:int) - Left pads a to length b (defaults to 2) with spaces
            * zpad(a, b:int) - Left pads a to length b (defaults to 2) with zeros

        Regular Expressions:
        If a regex is included, the match groups (0=whole match, >0=match group) are avaiable in a list 're' or 'regex'.
        Each match group is converted to an int if possible, so a zero padded int will lose the zeros.

        Examples:
            Input: S02E04.mp4
            Regex: S(\d+)E(\d+)

            Template: 'Season ${re[1]} Episode ${re[2]}.{ext}'
            Result: 'Season 2 Episode 4.mp4'

            Template: Template: 'Season ${re[1] | zpad} Episode ${zpad(re[2], 3)}.{ext}'
            Results: 'Season 02 Episode 004.mp4'


            Input: whatever.mp4
            Regex: S(\d+)E(\d)
            Template: 'Season ${ifempty(re[1], 'unknown')} Episode ${re[2]}.{ext}'
            Result: 'Season unknown Episode .mp4'
            """)

        rename_parser.add_argument('-x', '--regex', type=str, default=None)
        rename_parser.add_argument('--ignore-missing-regex', action='store_const', default=False, const=True,
                                   dest='ignore_missing_regex')
        rename_parser.add_argument('-i', '--index-start', type=int, default=1)
        rename_parser.add_argument('-o', '--output', default=None)
        rename_parser.add_argument('-r', '--recursive', action='store_const', default=False, const=True)
        rename_parser.add_argument('--filter-by-ext', type=str, default=None)
        rename_parser.add_argument('template')
        rename_parser.add_argument('input', nargs='+', help='Input files')

    def subexecute(self, ns):
        from texttable import Texttable
        from media_management_scripts.support.files import list_files
        from media_management_scripts.renamer import rename_process
        import os
        input_to_cmd = ns['input']
        template = ns['template']
        output = ns['output']
        regex = ns['regex']
        index_start = ns['index_start']
        recursive = ns['recursive']
        ignore_missing_regex = ns['ignore_missing_regex']
        filter_by_ext = ns['filter_by_ext']
        if recursive:
            if filter_by_ext:
                filter = lambda f: f.endswith(filter_by_ext)
            else:
                filter = lambda f: True
            files = []
            for f in input_to_cmd:
                if os.path.isdir(f):
                    files.extend(list_files(f, filter=filter))
                else:
                    files.append(f)
        else:
            files = input_to_cmd

        results = rename_process(template, files, index_start, output, regex,
                                 ignore_missing_regex=ignore_missing_regex)
        if ns['dry_run']:
            t = Texttable(max_width=0)
            t.set_deco(Texttable.VLINES | Texttable.HEADER)
            t.add_rows([('Source', 'Destination')] + results)
            print(t.draw())
        else:
            for src, dest in results:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                self._move(src, dest)


SubCommand.register(RenameCommand)
