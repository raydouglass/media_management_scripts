from . import SubCommand
from .common import *


class ConvertCommand(SubCommand):
    @property
    def name(self):
        return 'convert'

    def build_argparse(self, subparser):
        convert_parser = subparser.add_parser('convert', help='Convert to H.264 & AAC',
                                               parents=[parent_parser, input_parser, convert_parent_parser])

    def subexecute(self, ns):
        import os
        from media_management_scripts.convert import convert_with_config, convert_config_from_ns
        input_to_cmd = ns['input']
        output = ns['output']
        config = convert_config_from_ns(ns)
        if os.path.exists(output):
            print('Cowardly refusing to overwrite existing file: {}'.format(output))
        else:
            convert_with_config(input_to_cmd, output, config, print_output=True)


SubCommand.register(ConvertCommand)
