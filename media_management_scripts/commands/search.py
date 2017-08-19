from . import SubCommand
from .common import *
import argparse
import os


class SearchCommand(SubCommand):
    @property
    def name(self):
        return 'search'

    def build_argparse(self, subparser):
        search_parser = subparser.add_parser('search', parents=[parent_parser, input_parser],
                                             formatter_class=argparse.RawTextHelpFormatter,
                                             description="""
    Searches a directory for video files matching parameters.
    
    If a video has multiple streams, comparisons mean at least one stream matches.
    
    Available parameters:
    Video:
        v.codec - The video codec (h264, h265, mpeg2, etc)
        v.width - The video pixel width
        v.height - The video pixel height
    Audio:
        a.codec - The audio codec (aac, ac3)
        a.channels - The number of audio channels (stereo=2, 5.1=6, etc)
        a.lang - The language of the audio track
    Subtitles:
        s.codec - The subtitle codec (srt, hdmv_pgs, mov_text, etc)
        s.lang - The language of the subtitle track
    Others:
        ripped - Whether the video is marked as ripped or not
        bit_rate - The overall average bitrate
        resolution - The resolution name (LOW_DEF, HIGH_DEF, etc)
    Metadata:
        meta.xyz - Follows the basic JSON metadata output
    
    Examples:
        Find all videos that are H264
            v.codec = h264
        Find all videos that are H264 with stereo AAC
            v.codec = h264 and a.codec = aac and a.channels = 2
        Find all videos that are H265 or H264 and AAC
            a.codec = aac and (v.codec = h265 or v.codec = h264)
            a.codec = aac and v.codec in [h265, h264]
        Find all videos without English Subtitles
            s.lang != eng
        Find videos that are lower resolution than 1080
            v.height < 1080
""")
        search_parser.add_argument('--db', default=None, dest='db_file')
        search_parser.add_argument('query',
                                   help="The query to run. Recommended to enclose in single-quotes to avoid bash completions")
        search_parser.add_argument('-0', help='Output with null byte. Useful for piping into xargs -0.', action='store_const', const=True, default=False)

    def subexecute(self, ns):
        input_to_cmd = ns['input']
        null_byte = ns['0']
        query = ns['query']
        db_file = ns['db_file']
        l = []
        for file, metadata in search(input_to_cmd, query, db_file):
            if not null_byte:
                print(file)
            else:
                l.append(file)
        if null_byte:
            print('\0'.join(l))


SubCommand.register(SearchCommand)


class SearchParameters():
    def __init__(self, ns):
        from media_management_scripts.support.encoding import AudioChannelName
        self.video_codecs = set(ns['video_codec'].split(',')) if ns['video_codec'] else []
        self.audio_codecs = set(ns['audio_codec'].split(',')) if ns['audio_codec'] else []
        self.subtitles = set(ns['subtitle'].split(',')) if ns['subtitle'] else []
        self.audio_channels = []
        acs = set(ns['audio_channels'].split(',')) if ns['audio_channels'] else []
        for ac in acs:
            channel = AudioChannelName.from_name(ac)
            if not channel:
                raise Exception('Unknown AudioChannelName: {}'.format(ac))
            self.audio_channels.append(channel.num_channels)

        self.invert = ns['not']
        if ns['container']:
            raise Exception('Container not supported')
        if ns['resolution']:
            raise Exception('Resolution not supported')

    def match(self, metadata):
        video_matches = len(self.video_codecs) == 0
        for vs in metadata.video_streams:
            if vs.codec in self.video_codecs:
                video_matches = True

        audio_matches = len(self.audio_codecs) == 0
        audio_channel_matches = len(self.audio_channels) == 0
        for vs in metadata.audio_streams:
            if vs.codec in self.audio_codecs:
                audio_matches = True
            if vs.channels in self.audio_channels:
                audio_channel_matches = True

        st_matches = len(self.subtitles) == 0
        for vs in metadata.subtitle_streams:
            if vs.language in self.subtitles:
                st_matches = True

        result = video_matches and audio_matches and st_matches and audio_channel_matches
        if self.invert:
            return not result
        else:
            return result


def search(input_dir: str, query: str, db_file: str = None):
    from media_management_scripts.support.search_parser import parse
    from media_management_scripts.utils import create_metadata_extractor
    from media_management_scripts.support.files import list_files, movie_files_filter
    query = parse(query)
    with create_metadata_extractor(db_file) as extractor:
        for file in list_files(input_dir, movie_files_filter):
            path = os.path.join(input_dir, file)
            metadata = extractor.extract(path)
            context = {
                'v': {
                    'codec': [v.codec for v in metadata.video_streams],
                    'width': [v.width for v in metadata.video_streams],
                    'height': [v.height for v in metadata.video_streams]
                },
                'a': {
                    'codec': [a.codec for a in metadata.audio_streams],
                    'channels': [a.channels for a in metadata.audio_streams],
                    'lang': [a.language for a in metadata.audio_streams],
                },
                's': {
                    'codec': [s.codec for s in metadata.subtitle_streams],
                    'lang': [s.language for s in metadata.subtitle_streams]
                },
                'ripped': metadata.ripped,
                'bit_rate': metadata.bit_rate,
                'resolution': metadata.resolution._name_,
                'meta': metadata.to_0dict()

            }
            if query.exec(context) is True:
                yield (file, metadata)
