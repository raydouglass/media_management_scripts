from media_management_scripts.convert import convert_subtitles_to_srt
from . import SubCommand
from .common import *
import os


class SubtitlesCommand(SubCommand):
    @property
    def name(self):
        return 'subtitles'

    def build_argparse(self, subparser):
        subtitle_parser = subparser.add_parser('subtitles', help='Convert subtitles to SRT',
                                               parents=[parent_parser, input_parser])  # No input dir
        subtitle_parser.add_argument('--output', '-o', help='Output file or directory')
        subtitle_parser.add_argument('--no-ttml', help='Do not convert TTML', action='store_const', const=True,
                                     default=False)
        subtitle_parser.add_argument('--no-dfxp', help='Do not convert DFXP (Old TTML)', action='store_const', const=True,
                                     default=False)
        subtitle_parser.add_argument('--no-xml', help='Do not convert XML (treated as TTML)', action='store_const',
                                     const=True, default=False)
        subtitle_parser.add_argument('--no-vtt', help='Do not convert VTT', action='store_const', const=True,
                                     default=False)

    def _filter(self, file: str):
        if not self.ns['no_ttml']:
            if file.endswith('.ttml'):
                return True
        if not self.ns['no_dfxp']:
            if file.endswith('.dfxp'):
                return True
        if not self.ns['no_xml']:
            if file.endswith('.xml'):
                return True
        if not self.ns['no_vtt']:
            if file.endswith('.vtt'):
                return True
        return False

    def _get_io(self, input_to_cmd, output_dir):
        from media_management_scripts.support.files import get_input_output
        for i, o in get_input_output(input_to_cmd, output_dir, filter=self._filter):
            noext, _ = os.path.splitext(o)
            o = noext + '.srt'
            yield i, o

    def subexecute(self, ns):
        input_to_cmd = ns['input']
        output_dir = ns.get('output', None)

        if os.path.isfile(input_to_cmd):
            if not self._filter(input_to_cmd):
                raise Exception('File specified is filtered by arguments.')
            base = os.path.basename(input_to_cmd)
            noext, _ = os.path.splitext(base)
            if not output_dir:
                dir = os.path.dirname(input_to_cmd)
                output_dir = os.path.join(dir, noext + '.srt')

            self._bulk([(input_to_cmd, output_dir)], op=convert_subtitles_to_srt, column_descriptions=['Input', 'Output'])
        else:
            if not output_dir:
                output_dir = input_to_cmd
            results = list(self._get_io(input_to_cmd, output_dir))
            self._bulk(results, op=convert_subtitles_to_srt, column_descriptions=['Input', 'Output'])


SubCommand.register(SubtitlesCommand)
