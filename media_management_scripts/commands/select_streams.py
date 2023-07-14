from . import SubCommand
from .common import *
import argparse
import os


class SelectStreamsCommand(SubCommand):
    @property
    def name(self):
        return "select-streams"

    def build_argparse(self, subparser):
        input_parser = argparse.ArgumentParser(add_help=False)
        input_parser.add_argument("input", nargs="+", help="Input directory")

        stream_select_parser = subparser.add_parser(
            "select-streams",
            parents=[parent_parser, input_parser, convert_parent_parser, output_parser],
            help="Extract specific streams in a video file to a new file",
        )
        stream_select_parser.add_argument(
            "-c",
            "--convert",
            action="store_const",
            default=False,
            const=True,
            help="Whether to convert the file or just remux it",
        )
        stream_select_parser.add_argument(
            "-l",
            "--language",
            default="eng",
            help='Default language to select for audio and subtitle streams. Default is "eng"',
        )
        stream_select_parser.add_argument(
            "-a",
            "--auto",
            action="store_const",
            default=False,
            const=True,
            help="Whether to automatically select streams without prompting",
        )

    def subexecute(self, ns):
        from media_management_scripts.convert import convert_config_from_ns

        input_to_cmd = ns["input"]
        convert_config = convert_config_from_ns(ns) if ns["convert"] else None
        output_file = ns["output"]
        overwrite = ns["overwrite"]
        language = ns["language"]
        auto = ns["auto"]
        select_streams(
            input_to_cmd,
            output_file,
            overwrite=overwrite,
            convert_config=convert_config,
            language=language,
            auto=auto,
        )


SubCommand.register(SelectStreamsCommand)

from media_management_scripts.support.metadata import Stream
from media_management_scripts.utils import extract_metadata, ConvertConfig
from media_management_scripts.convert import convert_with_config, create_remux_args
from dialog import Dialog
from typing import Tuple, List


def video_to_str(v: Stream) -> Tuple[str, str, bool]:
    tag = str(v.index)
    if v.title:
        name = "{} ({}x{}) - {}".format(v.codec, v.width, v.height, v.title)
    else:
        name = "{} ({}x{})".format(v.codec, v.width, v.height)
    status = v.codec != "mjpeg"
    return (tag, name, status)


def audio_to_str(a: Stream, lang: str) -> Tuple[str, str, bool]:
    tag = str(a.index)
    if a.title:
        name = "{} ({}) - {} - {}".format(
            a.codec, a.channel_layout, a.language, a.title
        )
    else:
        name = "{} ({}) - {}".format(a.codec, a.channel_layout, a.language)
    status = a.language == lang or a.language == "unknown"
    return (tag, name, status)


def sub_to_str(
    s: Stream, lang: str, lang_override: str = None
) -> Tuple[str, str, bool]:
    tag = str(s.index)
    language = lang_override if lang_override else s.language
    if s.title:
        name = "{} ({}) - {}".format(language, s.codec, s.title)
    else:
        name = "{} ({})".format(language, s.codec)
    status = (
        language == lang or language == "unknown"
    ) and s.codec.lower() != "eia_608"
    return (tag, name, status)


def _get_stream_indexes(streams, title, text, converter, auto):
    d = Dialog(autowidgetsize=True)
    if len(streams) > 0:
        options = [converter(i) for i in streams]
        if auto:
            tags = [i[0] for i in options if i[2]]
        else:
            code, tags = d.checklist(title=title, text=text, choices=options)
            if code != d.OK:
                return
    else:
        tags = []
    return tags


def _get_all_stream_indexes(
    metadata, lang, lang_override=None, auto=False
) -> List[int]:
    title = os.path.basename(metadata.file)
    video_tags = _get_stream_indexes(
        metadata.video_streams, title, "Video Options", video_to_str, auto
    )
    audio_tags = _get_stream_indexes(
        metadata.audio_streams,
        title,
        "Audio Options",
        lambda a: audio_to_str(a, lang),
        auto,
    )
    sub_tags = _get_stream_indexes(
        metadata.subtitle_streams,
        title,
        "Subtitle Options",
        lambda s: sub_to_str(s, lang, lang_override),
        auto,
    )

    return video_tags, audio_tags, sub_tags


def select_streams(
    files,
    output_file,
    overwrite=False,
    convert_config: ConvertConfig = None,
    language="eng",
    auto: bool = False,
):
    from media_management_scripts.support.executables import execute_ffmpeg_with_dialog
    from media_management_scripts.support.combine_all import get_lang

    if not overwrite and os.path.exists(output_file):
        print("Output file exists: {}".format(output_file))
        return

    if any(file.endswith(".srt") for file in files) and not output_file.endswith(
        ".mkv"
    ):
        print("Cannot mix an SRT file into a non MKV output")
        return

    final_indexes = []
    max_duration = 0
    subtitle_index_tracker = 0
    output_meta = {}
    for i, file in enumerate(files):
        if file.endswith(".srt"):
            is_srt = True
            lang = get_lang(file)
            if lang is None:
                if auto:
                    lang = language
                else:
                    d = Dialog(autowidgetsize=True)
                    exit_code, lang = d.inputbox(
                        "Enter language", init="Unknown", title=os.path.basename(file)
                    )
                    if exit_code != d.OK:
                        return
        else:
            is_srt = False
            lang = None

        metadata = extract_metadata(file)
        if metadata.estimated_duration and metadata.estimated_duration > max_duration:
            max_duration = metadata.estimated_duration
        all_tags = _get_all_stream_indexes(
            metadata, language, lang_override=lang, auto=auto
        )
        if all_tags is not None:
            video_tags, audio_tags, subtitle_tags = all_tags
            indexes = video_tags + audio_tags + subtitle_tags
            final_indexes.extend(["{}:{}".format(i, index) for index in indexes])
            if is_srt and subtitle_tags:
                output_meta["s:{}".format(subtitle_index_tracker)] = {"language": lang}
            subtitle_index_tracker += len(subtitle_tags)
        else:
            # User selected cancel
            return

    if max_duration == 0:
        max_duration = None

    if convert_config:
        raise Exception("Convert is not supported in select-streams currently")
    elif len(final_indexes) > 0:
        args = create_remux_args(
            files,
            output_file,
            mappings=final_indexes,
            overwrite=overwrite,
            metadata=output_meta,
        )
        if len(files) == 1:
            title = os.path.basename(files[0])
        else:
            title = "Remuxing {} files".format(len(files))
        ret = execute_ffmpeg_with_dialog(args, duration=max_duration, title=title)
        if ret != 0:
            print("Error executing: {}".format(args))
    else:
        print("No streams selected.")
