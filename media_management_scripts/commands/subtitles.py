from media_management_scripts.convert import convert_subtitles_to_srt
from . import SubCommand
from .common import *
import os


class SubtitlesCommand(SubCommand):
    @property
    def name(self):
        return "subtitles"

    def build_argparse(self, subparser):
        subtitle_parser = subparser.add_parser(
            "subtitles",
            help="Convert subtitles to SRT",
            parents=[parent_parser, input_parser],
        )  # No input dir
        subtitle_parser.add_argument("--output", "-o", help="Output file or directory")
        subtitle_parser.add_argument(
            "--ext", help="Only convert files with these extensions", nargs="+"
        )

    def _filter(self, file: str):
        if self.ns.get("ext", None):
            for i in self.ns["ext"]:
                if file.endswith("." + i):
                    return True
            return False
        return True

    def _get_io(self, input_to_cmd, output_dir):
        from media_management_scripts.support.files import get_input_output

        for i, o in get_input_output(input_to_cmd, output_dir, filter=self._filter):
            noext, _ = os.path.splitext(o)
            o = noext + ".srt"
            yield i, o

    def subexecute(self, ns):
        input_to_cmd = ns["input"]
        output_dir = ns.get("output", None)

        if os.path.isfile(input_to_cmd):
            if not self._filter(input_to_cmd):
                raise Exception("File specified is filtered by arguments.")
            base = os.path.basename(input_to_cmd)
            noext, _ = os.path.splitext(base)
            if not output_dir:
                dir = os.path.dirname(input_to_cmd)
                output_dir = os.path.join(dir, noext + ".srt")

            self._bulk(
                [(input_to_cmd, output_dir)],
                op=convert_subtitles_to_srt,
                column_descriptions=["Input", "Output"],
            )
        else:
            if not output_dir:
                output_dir = input_to_cmd
            results = list(self._get_io(input_to_cmd, output_dir))
            self._bulk(
                results,
                op=convert_subtitles_to_srt,
                column_descriptions=["Input", "Output"],
            )


SubCommand.register(SubtitlesCommand)
