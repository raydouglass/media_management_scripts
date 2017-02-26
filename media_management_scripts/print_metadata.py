import os
from itertools import groupby

from media_management_scripts.utils import create_metadata_extractor, sizeof_fmt


def output(text, *args):
    return '   {}'.format(text).format(*args)


def duration_to_str(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return '%dh%02dm%02ds' % (h, m, s)
    else:
        return '%02dm%02ds' % (m, s)


def popup(text):
    applescript = """
    display dialog "{}"
    """.format(text)

    os.system("osascript -e '{}'".format(applescript))


def print_metadata(input, show_popup=False):
    extractor = create_metadata_extractor()
    meta = extractor.extract(input)
    o = []

    o.append(os.path.basename(input))
    o.append(output('Directory: {}', os.path.dirname(input)))
    size = os.path.getsize(input)
    o.append(output('Size: {}', sizeof_fmt(size)))

    durations = [float(s.duration) for s in meta.streams if s.duration]
    if len(durations) > 0:
        o.append(output('Duration: {}', duration_to_str(max(durations))))

    o.append(output('Bitrate: {:.2f} kb/s', float(meta.bit_rate) / 1024.0))
    for video in meta.video_streams:
        o.append(output('Video: {} ({}x{})', video.codec, video.width, video.height))
    audio_streams = []
    for audio in meta.audio_streams:
        audio_streams.append((audio.codec, audio.language))
    audio_streams.sort()
    result = []
    for key, valuesiter in groupby(audio_streams, key=lambda k: k[0]):
        result.append(dict(type=key, items=list(v[1] for v in valuesiter)))
    for r in result:
        o.append(output('Audio: {} ({})', r['type'], ', '.join(r['items'])))
    subtitles = [s.language for s in meta.subtitle_streams]
    if len(subtitles) == 0:
        subtitles = ['None']
    o.append(output('Subtitles: {}', ', '.join(subtitles)))
    o.append(output('Ripped: {}', meta.ripped))

    final = '\n'.join(o)
    if show_popup:
        popup(final)
    else:
        print(final)
