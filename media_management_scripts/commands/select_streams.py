from . import SubCommand
from .common import *


class SelectStreamsCommand(SubCommand):
    @property
    def name(self):
        return 'select-streams'

    def build_argparse(self, subparser):
        stream_select_parser = subparser.add_parser('select-streams',
                                                     parents=[parent_parser, input_parser, convert_parent_parser])
        stream_select_parser.add_argument('-c', '--convert', action='store_const', default=False, const=True,
                                          help='Whether to convert the file or just remux it')

    def subexecute(self, ns):
        from media_management_scripts.convert import convert_config_from_ns
        input_to_cmd = ns['input']
        convert_config = convert_config_from_ns(ns) if ns['convert'] else None
        output_file = ns['output']
        overwrite = ns['overwrite']
        select_streams(input_to_cmd, output_file, overwrite=overwrite, convert_config=convert_config)


SubCommand.register(SelectStreamsCommand)

from media_management_scripts.support.metadata import Stream
from media_management_scripts.utils import extract_metadata
from media_management_scripts.convert import ConvertConfig, convert_with_config, remux
from dialog import Dialog
from typing import Tuple, List


def video_to_str(v: Stream) -> Tuple[str, str, bool]:
    tag = str(v.index)
    if v.title:
        name = '{} ({}x{}) - {}'.format(v.codec, v.width, v.height, v.title)
    else:
        name = '{} ({}x{})'.format(v.codec, v.width, v.height)
    status = v.codec != 'mjpeg'
    return (tag, name, status)


def audio_to_str(a: Stream) -> Tuple[str, str, bool]:
    tag = str(a.index)
    if a.title:
        name = '{} ({}) - {} - {}'.format(a.codec, a.channel_layout, a.language, a.title)
    else:
        name = '{} ({}) - {}'.format(a.codec, a.channel_layout, a.language)
    status = a.language == 'eng' or a.language == 'unknown'
    return (tag, name, status)


def sub_to_str(s: Stream) -> Tuple[str, str, bool]:
    tag = str(s.index)
    if s.title:
        name = '{} ({}) - {}'.format(s.language, s.codec, s.title)
    else:
        name = '{} ({})'.format(s.language, s.codec)
    status = s.language == 'eng' or s.language == 'unknown'
    return (tag, name, status)


def _get_stream_indexes(metadata) -> List[int]:
    d = Dialog(autowidgetsize=True)

    if len(metadata.video_streams) > 0:
        video_options = [video_to_str(v) for v in metadata.video_streams]
        code, video_tags = d.checklist(text='Video Options', choices=video_options)
        if code != d.OK:
            return
    else:
        video_tags = []

    if len(metadata.audio_streams) > 0:
        audio_options = [audio_to_str(a) for a in
                         sorted(metadata.audio_streams, key=lambda s: s.channels, reverse=True)]

        code, audio_tags = d.checklist(text='Audio Options', choices=audio_options)
        if code != d.OK:
            return
    else:
        audio_tags = []

    if len(metadata.subtitle_streams) > 0:
        sub_options = [sub_to_str(a) for a in metadata.subtitle_streams]
        code, sub_tags = d.checklist(text='Subtitle Options', choices=sub_options)
        if code != d.OK:
            return
    else:
        sub_tags = []

    tags = video_tags + audio_tags + sub_tags
    return tags


def select_streams(file, output_file, overwrite=False, convert_config: ConvertConfig = None):
    metadata = extract_metadata(file)
    indexes = _get_stream_indexes(metadata)
    if indexes is None:
        return
    indexes = ['0:{}'.format(i) for i in indexes]
    if convert_config:
        raise Exception()
    else:
        remux(file, output_file, mappings=indexes, overwrite=overwrite, print_output=True)
