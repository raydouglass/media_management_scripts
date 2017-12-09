import os
import re
from media_management_scripts.support.files import get_input_output, mp4_mkv_filter
from media_management_scripts.convert import combine

LANG_PATTERN = re.compile('\.(\w+)\.srt')


def _filter(f: str):
    return mp4_mkv_filter(f) or f.endswith('.srt') or f.endswith('.idx')


def get_lang(srt_file):
    m = LANG_PATTERN.search(srt_file)
    if m:
        return m.group(1)
    return None


def combine_all(input, output, convert=False, crf=15, preset='veryfast', forced_language=None, lower_case=False):
    os.makedirs(output, exist_ok=True)
    files = {}
    for f, o in get_input_output(input, output, filter=_filter):
        filename = os.path.basename(f)
        if lower_case:
            filename = filename.lower()
        no_ext, ext = os.path.splitext(filename)
        lang = forced_language
        if not lang and (ext == '.srt' or ext == '.idx'):
            #  subtitle
            m = LANG_PATTERN.search(filename)
            if m:
                no_ext, lang = os.path.splitext(no_ext)
                lang = lang[1::]
        l = files.get(no_ext, [])
        l.append((f, ext, lang, o))
        files[no_ext] = l
    total = len(files)
    current = 1
    for k in sorted(files.keys()):
        print('Starting {} of {}: {}'.format(current, total, k))
        l = files[k]
        video_file = None
        output_file = None
        srt_file = None
        language = None
        for file, ext, lang, o in l:
            if ext == '.srt' or ext == '.idx':
                srt_file = file
                language = lang
            else:
                video_file = file
                output_file = o
                output_file = output_file.replace(ext, '.mkv')
        if not srt_file:
            print('No subtitles for {}'.format(video_file))
        elif not output_file:
            print('No video file for {}'.format(srt_file))
        else:
            combine(video_file, srt_file, output_file, crf=crf, preset=preset, convert=convert, lang=language)
        current += 1
