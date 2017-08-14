from . import SubCommand
from .common import *


class CombineSubtitlesCommand(SubCommand):
    @property
    def name(self):
        return 'combine-subtitles'

    def build_argparse(self, subparser):
        combine_video_subtitles_parser = subparser.add_parser('combine-subtitles',
                                                              help='Combine a video files with subtitle file',
                                                              parents=[parent_parser, input_parser,
                                                                       convert_parent_parser])
        combine_video_subtitles_parser.add_argument('input-subtitles', help='The subtitle file')
        combine_video_subtitles_parser.add_argument('--convert',
                                                    help='Whether to convert video streams to H.264 and audio to AAC',
                                                    action='store_const', const=True, default=False)

    def subexecute(self, ns):
        import sys
        from media_management_scripts.support.encoding import DEFAULT_CRF, DEFAULT_PRESET
        from media_management_scripts.convert import combine
        from media_management_scripts.support.combine_all import get_lang
        input_to_cmd = ns['input']
        srt_input = ns['input-subtitles']
        output = ns['output']
        if not output.endswith('.mkv'):
            print('Output must be a MKV file')
            sys.exit(1)
        crf = ns.get('crf', DEFAULT_CRF)
        preset = ns.get('preset', DEFAULT_PRESET)
        convert = ns.get('convert', False)
        lang = get_lang(srt_input)
        combine(input_to_cmd, srt_input, output, convert=convert, crf=crf, preset=preset, lang=lang)


SubCommand.register(CombineSubtitlesCommand)


class CombineSubtitlesDirectoryCommand(SubCommand):
    @property
    def name(self):
        return 'combine-all'

    def build_argparse(self, subparser):
        combine_all_parser = subparser.add_parser('combine-all',
                                                  help='Combine a directory tree of video files with subtitle file',
                                                  parents=[parent_parser, input_parser, convert_parent_parser])
        combine_all_parser.add_argument('--convert',
                                        help='Whether to convert video streams to H.264 and audio to AAC',
                                        action='store_const', const=True, default=False)

    def subexecute(self, ns):
        from media_management_scripts.support.encoding import DEFAULT_CRF, DEFAULT_PRESET
        from media_management_scripts.support.combine_all import combine_all
        input_to_cmd = ns['input']
        crf = ns.get('crf', DEFAULT_CRF)
        preset = ns.get('preset', DEFAULT_PRESET)
        convert = ns.get('convert', False)
        output = ns['output']
        combine_all(input_to_cmd, output, convert, crf, preset)


SubCommand.register(CombineSubtitlesDirectoryCommand)
