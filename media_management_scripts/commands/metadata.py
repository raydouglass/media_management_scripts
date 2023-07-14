from . import SubCommand
from .common import *


class MetadataCommand(SubCommand):
    @property
    def name(self):
        return "metadata"

    def build_argparse(self, subparser):
        metadata_parser = subparser.add_parser(
            self.name,
            help="Show metadata for a file",
            parents=[parent_parser, input_parser],
        )
        metadata_group = metadata_parser.add_mutually_exclusive_group()
        metadata_group.add_argument(
            "--popup",
            action="store_const",
            const=True,
            default=False,
            help="Show the metadata in a popup (MacOS only)",
        )
        metadata_group.add_argument(
            "--json", "-j", action="store_const", const=True, default=False
        )
        metadata_parser.add_argument(
            "--interlace",
            help="Try to detect interlacing",
            choices=["none", "summary", "report"],
            default="none",
        )

    def subexecute(self, ns):
        input_to_cmd = ns["input"]
        if ns["json"]:
            print_metadata_json(input_to_cmd, ns["interlace"])
        else:
            print_metadata(input_to_cmd, ns["popup"], ns["interlace"])


SubCommand.register(MetadataCommand)

import os
import json
from itertools import groupby

from media_management_scripts.utils import create_metadata_extractor
from media_management_scripts.support.formatting import (
    sizeof_fmt,
    duration_to_str,
    bitrate_to_str,
)


def output(text, *args):
    return "   {}".format(text).format(*args)


def popup(text):
    applescript = """
    display dialog "{}"
    """.format(
        text
    ).replace(
        '"', '\\"'
    )

    os.system('osascript -e "{}"'.format(applescript))


class Encoder(json.JSONEncoder):
    def default(self, o):
        return o.to_dict()


def print_metadata_json(input, interlace="none"):
    extractor = create_metadata_extractor()
    meta = extractor.extract(input, interlace != "none")
    print(json.dumps(meta, cls=Encoder))


def print_metadata(input, show_popup=False, interlace="none"):
    extractor = create_metadata_extractor()
    meta = extractor.extract(input, interlace != "none")
    o = []

    o.append(os.path.basename(input))
    o.append(output("Directory: {}", os.path.dirname(input)))
    size = os.path.getsize(input)
    if meta.title:
        o.append(output("Title: {}", meta.title))
    o.append(output("Size: {}", sizeof_fmt(size)))
    o.append(output("Format: {}", meta.format))

    durations = [float(s.duration) for s in meta.streams if s.duration]
    if len(durations) > 0:
        o.append(output("Duration: {}", duration_to_str(max(durations))))

    o.append(output("Bitrate: {}", bitrate_to_str(meta.bit_rate)))
    for video in meta.video_streams:
        if video.bit_depth:
            o.append(
                output(
                    "Video: {} {} bit ({}x{})",
                    video.codec,
                    video.bit_depth,
                    video.width,
                    video.height,
                )
            )
        else:
            o.append(
                output("Video: {} ({}x{})", video.codec, video.width, video.height)
            )

    audio_streams = []
    for audio in meta.audio_streams:
        audio_streams.append((audio.codec, audio.language, audio.channel_layout))
    audio_streams.sort()
    o.append(output("Audio:"))
    for a in audio_streams:
        o.append(output("  {} ({}, {})", *a))

    subtitles = [s.language for s in meta.subtitle_streams]
    if len(subtitles) == 0:
        subtitles = ["None"]
    o.append(output("Subtitles: {}", ", ".join(subtitles)))
    o.append(output("Ripped: {}", meta.ripped))

    if meta.interlace_report:
        if interlace == "summary":
            o.append(output("Interlaced: {}", meta.interlace_report.is_interlaced()))
        elif interlace == "report":
            o.append(output("Interlaced:"))
            single = meta.interlace_report.single
            o.append(
                output(
                    "  Single: TFF={}, BFF={}, Progressive={}, Undetermined={} ({:.2f}%)",
                    single.tff,
                    single.bff,
                    single.progressive,
                    single.undetermined,
                    single.ratio * 100,
                )
            )
            multi = meta.interlace_report.multi
            o.append(
                output(
                    "  Multi: TFF={}, BFF={}, Progressive={}, Undetermined={} ({:.2f}%)",
                    multi.tff,
                    multi.bff,
                    multi.progressive,
                    multi.undetermined,
                    multi.ratio * 100,
                )
            )

    final = "\n".join(o)
    if show_popup:
        popup(final)
    else:
        print(final)
