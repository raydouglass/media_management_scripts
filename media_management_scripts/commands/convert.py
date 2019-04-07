from . import SubCommand
from .common import *
import argparse
from media_management_scripts.support.files import get_input_output
from media_management_scripts.convert import convert_with_config


def _bulk_convert(i, o, config):
    print('Starting {}'.format(i))
    convert_with_config(i, o, config, print_output=False)


class ConvertCommand(SubCommand):
    @property
    def name(self):
        return 'convert'

    def build_argparse(self, subparser):
        desc="""
    Converts a video file to 'standard' parameters. By default, this is H264 with AAC audio.
    
    Convert to HEVC/H.265:
        convert --video-codec hevc <input> <output>
    Convert to HEVC with AC3 audio:
        convert --video-codec hevc --audio-codec ac3 <input> <output>
    Convert to HEVC, but don't convert audio:
        convert --video-codec hevc --audio-codec copy <input> <output>
    Scale to 480p
        convert --scale 480
        """


        convert_parser = subparser.add_parser('convert', help='Convert a file',
                                              parents=[parent_parser, input_parser, convert_parent_parser, output_parser],
                                              formatter_class=argparse.RawTextHelpFormatter,
                                              description=desc)
        convert_parser.add_argument('--bulk', help='Enables bulk conversion mode', action='store_const', const=True,
                                    default=False)

    def subexecute(self, ns):
        import os
        from media_management_scripts.convert import convert_config_from_ns
        input_to_cmd = ns['input']
        output = ns['output']
        bulk = ns['bulk']
        config = convert_config_from_ns(ns)

        if os.path.isdir(input_to_cmd):
            if bulk:
                os.makedirs(output, exist_ok=True)
                files = list(get_input_output(input_to_cmd, output))
                self._bulk(files, lambda i, o: _bulk_convert(i, o, config), ['Input', 'Output'])
            else:
                print('Cowardly refusing to convert a direction without --bulk flag')
        elif os.path.exists(output):
            print('Cowardly refusing to overwrite existing file: {}'.format(output))
        else:
            convert_with_config(input_to_cmd, output, config, print_output=True)


SubCommand.register(ConvertCommand)
