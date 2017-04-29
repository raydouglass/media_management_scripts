from media_management_scripts.utils import create_metadata_extractor
from media_management_scripts.utils import find_files, MOVIE_FILES
from media_management_scripts.support.encoding import AudioChannelName


class SearchParameters():
    def __init__(self, ns):
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


def search(input_dir, search_params):
    extractor = create_metadata_extractor()
    for file in find_files(input_dir, MOVIE_FILES):
        metadata = extractor.extract(file)
        if search_params.match(metadata):
            yield (file, metadata)
