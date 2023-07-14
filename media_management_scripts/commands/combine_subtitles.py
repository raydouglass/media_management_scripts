from . import SubCommand
from .common import *


class CombineSubtitlesCommand(SubCommand):
    @property
    def name(self):
        return "combine-subtitles"

    def build_argparse(self, subparser):
        combine_video_subtitles_parser = subparser.add_parser(
            "combine-subtitles",
            help="Combine a video files with subtitle file",
            parents=[parent_parser, convert_parent_parser],
        )
        combine_video_subtitles_parser.add_argument(
            "input", help="The input video file"
        )
        combine_video_subtitles_parser.add_argument(
            "input-subtitles", help="The subtitle file"
        )
        combine_video_subtitles_parser.add_argument(
            "output", help="The destination file"
        )
        combine_video_subtitles_parser.add_argument(
            "--convert",
            help="Whether to convert video streams to H.264 and audio to AAC",
            action="store_const",
            const=True,
            default=False,
        )
        combine_video_subtitles_parser.add_argument(
            "-l", "--language", help="Set the language to use"
        )

    def subexecute(self, ns):
        import sys
        from media_management_scripts.support.encoding import (
            DEFAULT_CRF,
            DEFAULT_PRESET,
        )
        from media_management_scripts.convert import combine
        from media_management_scripts.support.combine_all import get_lang

        input_to_cmd = ns["input"]
        srt_input = ns["input-subtitles"]
        output = ns["output"]
        if not output.endswith(".mkv"):
            print("Output must be a MKV file")
            sys.exit(1)
        crf = ns.get("crf", DEFAULT_CRF)
        preset = ns.get("preset", DEFAULT_PRESET)
        convert = ns.get("convert", False)
        lang = ns.get("language") if "language" in ns else get_lang(srt_input)
        combine(
            input_to_cmd,
            srt_input,
            output,
            convert=convert,
            crf=crf,
            preset=preset,
            lang=lang,
        )


SubCommand.register(CombineSubtitlesCommand)


class CombineSubtitlesDirectoryCommand(SubCommand):
    @property
    def name(self):
        return "combine-all"

    def build_argparse(self, subparser):
        combine_all_parser = subparser.add_parser(
            "combine-all",
            help="Combine a directory tree of video files with subtitle file",
            parents=[parent_parser, input_parser, convert_parent_parser],
        )
        combine_all_parser.add_argument(
            "--convert",
            help="Whether to convert video streams to H.264 and audio to AAC",
            action="store_const",
            const=True,
            default=False,
        )
        combine_all_parser.add_argument(
            "-l", "--language", help="Set the language to use"
        )
        combine_all_parser.add_argument(
            "--lower-case",
            "--lc",
            help="Whether to compare videos and subtitles files by lower case",
            action="store_const",
            const=True,
            default=False,
            dest="lower-case",
        )

    def subexecute(self, ns):
        from media_management_scripts.support.encoding import (
            DEFAULT_CRF,
            DEFAULT_PRESET,
        )
        from media_management_scripts.support.combine_all import (
            combine_all,
            get_combinable_files,
        )

        input_to_cmd = ns["input"]
        crf = ns.get("crf", DEFAULT_CRF)
        preset = ns.get("preset", DEFAULT_PRESET)
        convert = ns.get("convert", False)
        output = ns["output"]
        language = ns.get("language", None)
        lower_case = ns.get("lower-case", False)
        files = get_combinable_files(input_to_cmd, output, language, lower_case)
        if self.dry_run:
            self._bulk_print(
                list(files), ["Video File", "Subtitle File", "Language", "Output"]
            )
        else:
            combine_all(files, convert, crf, preset)


SubCommand.register(CombineSubtitlesDirectoryCommand)
