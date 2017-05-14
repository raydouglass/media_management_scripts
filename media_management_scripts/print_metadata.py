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


def print_metadata(input, show_popup=False, interlace='none'):
    extractor = create_metadata_extractor()
    meta = extractor.extract(input, interlace != 'none')
    o = []

    o.append(os.path.basename(input))
    o.append(output('Directory: {}', os.path.dirname(input)))
    size = os.path.getsize(input)
    if meta.title:
        o.append(output('Title: {}', meta.title))
    o.append(output('Size: {}', sizeof_fmt(size)))
    o.append(output('Format: {}', meta.format))

    durations = [float(s.duration) for s in meta.streams if s.duration]
    if len(durations) > 0:
        o.append(output('Duration: {}', duration_to_str(max(durations))))

    o.append(output('Bitrate: {:.2f} kb/s', float(meta.bit_rate) / 1024.0))
    for video in meta.video_streams:
        o.append(output('Video: {} ({}x{})', video.codec, video.width, video.height))

    audio_streams = []
    for audio in meta.audio_streams:
        audio_streams.append((audio.codec, audio.language, audio.channel_layout))
    audio_streams.sort()
    o.append(output('Audio:'))
    for a in audio_streams:
        o.append(output('  {} ({}, {})', *a))

    subtitles = [s.language for s in meta.subtitle_streams]
    if len(subtitles) == 0:
        subtitles = ['None']
    o.append(output('Subtitles: {}', ', '.join(subtitles)))
    o.append(output('Ripped: {}', meta.ripped))

    if interlace == 'summary':
        o.append(output('Interlaced: {}', meta.interlace_report.is_interlaced()))
    elif interlace == 'report':
        o.append(output('Interlaced:'))
        single = meta.interlace_report.single
        o.append(output('  Single: TFF={}, BFF={}, Progressive={}, Undetermined={} ({:.2f}%)', single.tff, single.bff,
                        single.progressive, single.undetermined, single.ratio * 100))
        multi = meta.interlace_report.multi
        o.append(output('  Multi: TFF={}, BFF={}, Progressive={}, Undetermined={} ({:.2f}%)', multi.tff, multi.bff,
                        multi.progressive, multi.undetermined, multi.ratio * 100))

    final = '\n'.join(o)
    if show_popup:
        popup(final)
    else:
        print(final)
