from . import SubCommand
from .common import *


class SplitCommand(SubCommand):
    @property
    def name(self):
        return 'split'

    def build_argparse(self, subparser):
        split_parser = subparser.add_parser('split', help='Split a file', parents=[parent_parser, input_parser])
        split_parser.add_argument('-c', '--by-chapters', help='Split file by chapters, specifying number of episodes',
                                  type=int)
        split_parser.add_argument('--output', '-o', default='./', dest='output')

    def subexecute(self, ns):
        from media_management_scripts.support.split import split_by_chapter
        input_to_cmd = ns['input']
        output = ns['output']
        if 'by_chapters' in ns:
            episodes = ns['by_chapters']
            split_by_chapter(input_to_cmd, output, episodes)
        else:
            raise Exception('Unsupported')


SubCommand.register(SplitCommand)
