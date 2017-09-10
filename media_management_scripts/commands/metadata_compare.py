from . import SubCommand
from .common import *
import os


class MetadataCompareCommand(SubCommand):
    @property
    def name(self):
        return 'compare'

    def build_argparse(self, subparser):
        metadata_parser = subparser.add_parser(self.name, help='Show metadata for a file',
                                               parents=[parent_parser])
        metadata_parser.add_argument('--interlace', help='Try to detect interlacing',
                                     choices=['none', 'summary', 'report'], default='none')
        metadata_parser.add_argument('input', nargs='+')

    def subexecute(self, ns):
        from media_management_scripts.utils import create_metadata_extractor
        from media_management_scripts.support.formatting import sizeof_fmt, duration_to_str
        input_to_cmd = ns['input']
        interlace = ns['interlace']
        extractor = create_metadata_extractor()
        metadatas = [extractor.extract(i, interlace != 'none') for i in input_to_cmd]
        header = [''] + [os.path.basename(f.file) for f in metadatas]
        num_audio = max([len(m.audio_streams) for m in metadatas])
        rows = ['Size', 'Duration', 'Bitrate (kb/s)', 'Video Codec', 'Resolution', 'Audio']
        for i in range(1, num_audio):
            rows.append('')
        rows.append('Subtitles')
        file_columns = [rows]
        for m in metadatas:
            data = []
            data.append(sizeof_fmt(os.path.getsize(m.file)))
            data.append(duration_to_str(m.estimated_duration) if m.estimated_duration else '')
            data.append('{:.2f}'.format(m.bit_rate / 1024.0))
            video = m.video_streams[0]
            data.append(video.codec)
            data.append('{}x{}'.format(video.width, video.height))
            for a in m.audio_streams:
                data.append('{} ({}, {})'.format(a.codec, a.language, a.channel_layout))
            for i in range(len(m.audio_streams), num_audio):
                data.append('')
            data.append(','.join([s.language for s in m.subtitle_streams]))
            file_columns.append(data)
        table = list(map(list, zip(*file_columns)))
        self._bulk_print(table, header)


SubCommand.register(MetadataCompareCommand)
