from . import SubCommand
from .common import *


class ConcatMp4Command(SubCommand):
    @property
    def name(self):
        return 'concat-mp4'

    def build_argparse(self, subparser):
        concat_mp4_parser = subparser.add_parser('concat-mp4', help='Concat multiple mp4 files together',
                                                 parents=[])  # No input dir
        concat_mp4_parser.add_argument('output', help='The output file')
        concat_mp4_parser.add_argument('input', nargs='*',
                                       help='The input files to concat. These must be mp4 with h264 codec.')

    def subexecute(self, ns):
        import media_management_scripts.support.concat_mp4
        input_to_cmd = ns['input']
        output_file = ns['output']
        media_management_scripts.support.concat_mp4(output_file, input_to_cmd)


SubCommand.register(ConcatMp4Command)
