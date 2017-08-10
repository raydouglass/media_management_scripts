# ffprobe -show_streams -show_format -print_format json {}

import subprocess
import json
import copy
import os
import re
import operator
from typing import List, Tuple
from media_management_scripts.support.encoding import Resolution, resolution_name
from media_management_scripts.support.interlace import find_interlace, InterlaceReport
from media_management_scripts.support.formatting import sizeof_fmt, duration_to_str
import shelve

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


class Metadata():
    def __init__(self, file, ffprobe_output, interlace_report: InterlaceReport = None):
        self.file = file
        self._ffprobe_output = ffprobe_output
        self.interlace_report = interlace_report
        if 'streams' not in ffprobe_output:
            raise Exception('Invalid ffprobe output ({}): {}'.format(file, ffprobe_output))
        self.streams = [Stream(s) for s in ffprobe_output['streams']]
        format = ffprobe_output['format']
        self.size = float(format['size'])
        self.bit_rate = float(format['bit_rate'])
        self.format = format['format_name']
        self.format_long_name = format['format_long_name']
        self.tags = copy.copy(format.get('tags', {}))
        self.title = self.tags.get('title', None)
        if not self.title:
            self.title = self.tags.get('Title', None)
        self.audio_streams = [s for s in self.streams if s.is_audio()]
        self.video_streams = [s for s in self.streams if s.is_video()]
        self.subtitle_streams = [s for s in self.streams if s.is_subtitle()]

        durs = [s.duration for s in self.streams if s.duration]
        self.estimated_duration = max(durs) if durs else None

        if self.video_streams:
            max_height = max([s.height for s in self.video_streams])
            self.resolution = resolution_name(max_height)
        else:
            self.resolution = None

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

    def to_dict(self):
        return {
            'file': self.file,
            'title': self.title,
            'duration': duration_to_str(self.estimated_duration) if self.estimated_duration else None,
            'size': sizeof_fmt(self.size),
            'resolution': self.resolution._name_,
            'bit_rate': self.bit_rate,
            'ripped': self.ripped,
            'format': self.format,
            'format_long_name': self.format_long_name,
            'tags': self.tags,
            'streams': [s.to_dict() for s in self.streams],
            'chapters': [c.to_dict() for c in self.chapters] if self.chapters else [],
            'interlace': self.interlace_report.to_dict() if self.interlace_report else None
        }

    def __repr__(self):
        return '<Metadata: file={}, streams={}, format={}, size={}>'.format(self.file, len(self.streams), self.format,
                                                                            self.size)


class Chapter():
    def __init__(self, chapter):
        self.id = chapter['id']
        self.start_time = float(chapter['start_time'])
        self.end_time = float(chapter['end_time'])
        self.title = chapter['tags'].get('title', None)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'start': duration_to_str(self.start_time),
            'end': duration_to_str(self.end_time)
        }

    def __repr__(self):
        return '<Chapter start={}, end={}, title={}>'.format(self.start_time, self.end_time, self.title)


class Stream():
    def __init__(self, stream):
        self.index = stream['index']
        self.codec = stream['codec_name']
        self.codec_long_name = stream['codec_long_name']
        self.codec_type = stream['codec_type']
        self.width = int(stream['width']) if 'width' in stream else None
        self.height = int(stream['height']) if 'height' in stream else None
        self.tags = copy.copy(stream.get('tags', {}))
        self.title = self.tags.get('title', None)
        if not self.title:
            self.title = self.tags.get('Title', None)
        self.language = self.tags.get('language', self.tags.get('LANGUAGE', 'unknown'))
        self.duration = float(stream['duration']) if 'duration' in stream else None
        self._data = stream
        if self.is_audio():
            self.channels = int(stream['channels']) if 'channels' in stream else None
            self.channel_layout = stream.get('channel_layout', None)
        if not self.duration and 'DURATION' in self.tags:
            parts = [float(s) for s in self.tags['DURATION'].split(':')]
            self.duration = parts[0] * 60 * 60 + parts[1] * 60 + parts[2]

    def is_audio(self):
        return self.codec_type == 'audio'

    def is_video(self):
        return self.codec_type == 'video'

    def is_subtitle(self):
        return self.codec_type == 'subtitle'

    @property
    def type(self):
        return 'audio' if self.is_audio() else (
            'video' if self.is_video() else ('subtitle' if self.is_subtitle() else None))

    def to_dict(self):
        d = {
            'index': self.index,
            'type': self.type,
            'codec': self.codec,
            'codec_long_name': self.codec_long_name,
            'duration': duration_to_str(self.duration) if self.duration else None
        }
        if self.is_audio():
            d['channels'] = self.channels
            d['channel_layout'] = self.channel_layout
        if self.is_audio() or self.is_subtitle():
            d['language'] = self.language
        if self.is_video():
            d['width'] = self.width
            d['height'] = self.height
        d['tags'] = self.tags
        return d

    def __repr__(self):
        return '<Stream: index={}, codec={}, type={}, lang={}, width={}, height={}>'.format(self.index, self.codec,
                                                                                            self.codec_type,
                                                                                            self.language, self.width,
                                                                                            self.height)


class MetadataExtractor():
    def __init__(self, extractor_config, db_file=None):
        self._ffprobe_exe = extractor_config['ffprobe_exe']
        self.extractor_attributes = {'title': 'Title'}
        if db_file:
            self.db = shelve.open(db_file)
        else:
            self.db = None

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.db is not None:
            self.db.close()

    def _execute(self, file):
        args = [self._ffprobe_exe, '-v', 'quiet', '-show_chapters', '-show_streams', '-show_format', '-print_format',
                'json', file]
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        p.wait()
        if stderr:
            raise Exception(stderr)
        return json.loads(stdout.decode('UTF-8'))

    def extract(self, file, detect_interlace=False) -> Metadata:
        if self.db is not None and file in self.db:
            output = self.db[file]
        else:
            if not os.path.isfile(file):
                raise FileNotFoundError(file)
            output = self._execute(file)
            if self.db is not None:
                self.db[file] = output

        metadata = Metadata(file, output)
        if detect_interlace:
            interlace_report = find_interlace(file, metadata=metadata)
        else:
            interlace_report = None

        metadata.interlace_report = interlace_report
        return metadata

    def add_interlace_report(self, metadata: Metadata):
        if metadata.interlace_report is None:
            metadata.interlace_report = find_interlace(metadata.file, metadata=metadata)
        return metadata
