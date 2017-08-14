from . import SubCommand
from .common import *


class StripYoutubeDlCommand(SubCommand):
    @property
    def name(self):
        return 'strip-youtube-dl'

    def build_argparse(self, subparser):
        subparser.add_parser('strip-youtube-dl', help='Remove the playlist index prefix from files',
                             parents=[parent_parser, input_parser])

    def subexecute(self, ns):
        import re, os
        input_to_cmd = ns['input']
        pattern = re.compile('\d+ - .+\.mp4')
        for root, subdirs, files in os.walk(input_to_cmd):
            for file in files:
                source = os.path.join(root, file)
                if pattern.match(file):
                    index = file.index(' - ')
                    out_path = os.path.join(root, file[index + 3::])
                    print('{} -> {}'.format(source, out_path))
                    if not ns['dry_run']:
                        self._move(source, out_path)


SubCommand.register(StripYoutubeDlCommand)
