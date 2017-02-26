# ffprobe -show_streams -show_format -print_format json {}

import subprocess
import json
import copy
import os
import re
import operator
from typing import List, Tuple
from media_management_scripts.support.encoding import Resolution, resolution_name

DATE_PATTERN = re.compile('\d{4}_\d{2}_\d{2}')
ONLY_DATE_PATTERN = re.compile('^\d{4}-\d{2}-\d{2}$')

ATTRIBUTE_KEY_TITLE = 'title'
ATTRIBUTE_KEY_SUBTITLE = 'subtitle'
ATTRIBUTE_KEY_DESCRIPTION = 'description'
ATTRIBUTE_KEY_AIR_DATE = 'air_date'
ATTRIBUTE_KEY_NETWORK = 'network'
ATTRIBUTE_KEY_GENRE = 'genre'

WTV_ATTRIBUTES = {
    ATTRIBUTE_KEY_TITLE: 'Title',
    ATTRIBUTE_KEY_SUBTITLE: 'WM/SubTitle',
    ATTRIBUTE_KEY_DESCRIPTION: 'WM/SubTitleDescription',
    ATTRIBUTE_KEY_AIR_DATE: 'WM/MediaOriginalBroadcastDateTime',
    ATTRIBUTE_KEY_NETWORK: 'service_provider'
}

GENERIC_ATTRIBUTES = {
    ATTRIBUTE_KEY_TITLE: 'title'
}

FORMATS = {
    'wtv': WTV_ATTRIBUTES,
}


class MetadataExtractor():
    def __init__(self, extractor_config):
        self._ffprobe_exe = extractor_config['ffprobe_exe']
        self.extractor_attributes = {'title': 'Title'}

    def _execute(self, file):
        args = [self._ffprobe_exe, '-v', 'quiet', '-show_chapters', '-show_streams', '-show_format', '-print_format',
                'json', file]
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        p.wait()
        if stderr:
            raise Exception(stderr)
        return json.loads(stdout.decode('UTF-8'))

    def extract(self, file):
        if not os.path.isfile(file):
            raise FileNotFoundError(file)
        output = self._execute(file)
        return Metadata(file, output)


class Metadata():
    def __init__(self, file, ffprobe_output):
        self.file = file
        self.streams = [Stream(s) for s in ffprobe_output['streams']]
        format = ffprobe_output['format']
        self.size = format['size']
        self.bit_rate = format['bit_rate']
        self.format = format['format_name']
        self.format_long_name = format['format_long_name']
        self.tags = copy.copy(format.get('tags', {}))
        self._output = ffprobe_output
        self.audio_streams = [s for s in self.streams if s.is_audio()]
        self.video_streams = [s for s in self.streams if s.is_video()]
        self.subtitle_streams = [s for s in self.streams if s.is_subtitle()]

        max_height = max([s.height for s in self.video_streams])
        self.resolution = resolution_name(max_height)

        self.chapters = [Chapter(c) for c in ffprobe_output['chapters']]
        self.chapters.sort(key=lambda c: float(c.start_time))

        self.ripped = False
        for s in self.video_streams:
            if 'RIPPED' in s.tags or 'ripped' in s.tags:
                is_ripped = s.tags.get('ripped', s.tags.get('RIPPED'))
                if is_ripped in (True, 'True', 'true', '"true"'):
                    self.ripped = True
                    break

    def __getattr__(self, item):
        attributes = FORMATS.get(self.format, GENERIC_ATTRIBUTES)
        attr_key = None
        if item == 'title':
            attr_key = ATTRIBUTE_KEY_TITLE
        elif item == 'subtitle':
            attr_key = ATTRIBUTE_KEY_SUBTITLE
        elif item == 'description':
            attr_key = ATTRIBUTE_KEY_DESCRIPTION
        elif item == 'air_date':
            attr_key = ATTRIBUTE_KEY_AIR_DATE
        else:
            raise AttributeError()
        if attr_key in attributes:
            key = attributes[attr_key]
            return self.tags.get(key, None)
        else:
            return None

    def get_air_date(self, parse_from_filename=False):
        air_date = self.air_date
        if parse_from_filename and (not air_date or air_date == '0001-01-01T00:00:00Z'):
            filename = os.path.basename(self.file)
            match = DATE_PATTERN.search(filename)
            if match:
                air_date = match.group().replace('_', '-')
        if not ONLY_DATE_PATTERN.match(air_date):
            air_date = air_date.split('T')[0]
        return air_date

    def __repr__(self):
        return '<Metadata: file={}, streams={}, format={}, size={}>'.format(self.file, len(self.streams), self.format,
                                                                            self.size)


class Chapter():
    def __init__(self, chapter):
        self.id = chapter['id']
        self.start_time = chapter['start_time']
        self.end_time = chapter['end_time']
        self.title = chapter['tags'].get('title', None)

    def __repr__(self):
        return '<Chapter start={}, end={}, title={}>'.format(self.start_time, self.end_time, self.title)


class Stream():
    def __init__(self, stream):
        self.index = stream['index']
        self.codec = stream['codec_name']
        self.codec_long_name = stream['codec_long_name']
        self.codec_type = stream['codec_type']
        self.width = stream.get('width', None)
        self.height = stream.get('height', None)
        self.tags = copy.copy(stream.get('tags', {}))
        self.language = self.tags.get('language', 'unknown')
        self.duration = stream.get('duration', None)
        self._data = stream
        if self.is_audio():
            self.audio_channels = stream.get('channels', None)

    def is_audio(self):
        return self.codec_type == 'audio'

    def is_video(self):
        return self.codec_type == 'video'

    def is_subtitle(self):
        return self.codec_type == 'subtitle'

    def __repr__(self):
        return '<Stream: index={}, codec={}, type={}, lang={}, width={}, height={}>'.format(self.index, self.codec,
                                                                                            self.codec_type,
                                                                                            self.language, self.width,
                                                                                            self.height)
