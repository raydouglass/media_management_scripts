import os
import re
from media_management_scripts.support.files import get_input_output, movie_files_filter
from media_management_scripts.convert import combine

LANG_PATTERN = re.compile(r"\.(\w+)\.(srt|idx|ttml)")

subtitle_exts = (".srt", ".idx", ".ttml")


def _filter(f: str):
    return (
        movie_files_filter(f)
        or f.endswith(".srt")
        or f.endswith(".idx")
        or f.endswith(".ttml")
    )


def get_lang(srt_file):
    m = LANG_PATTERN.search(srt_file)
    if m:
        return m.group(1)
    return None


def get_combinable_files(input_dir, output_dir, forced_language=None, lower_case=False):
    files = {}
    for f, o in get_input_output(input_dir, output_dir, filter=_filter):
        filename = os.path.basename(f)
        if lower_case:
            filename = filename.lower()
        no_ext, ext = os.path.splitext(f)
        lang = forced_language
        if not lang and ext in subtitle_exts:
            #  subtitle
            m = LANG_PATTERN.search(filename)
            if m:
                no_ext, lang = os.path.splitext(no_ext)
                lang = lang[1::]
        l = files.get(no_ext, [])
        l.append((f, ext, lang, o))
        files[no_ext] = l
    for k in sorted(files.keys()):
        l = files[k]
        video_file = None
        output_file = None
        srt_file = None
        language = None
        for file, ext, lang, o in l:
            if ext in subtitle_exts:
                srt_file = file
                language = lang
            else:
                video_file = file
                output_file = o
                output_file = output_file.replace(ext, ".mkv")
        yield video_file, srt_file, language, output_file


def combine_all(files, convert=False, crf=15, preset="veryfast"):
    for video_file, srt_file, language, output_file in files:
        print("Starting {}".format(video_file))
        if not srt_file:
            print("No subtitles for {}".format(video_file))
        elif not output_file:
            print("No video file for {}".format(srt_file))
        else:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            combine(
                video_file,
                srt_file,
                output_file,
                crf=crf,
                preset=preset,
                convert=convert,
                lang=language,
            )
