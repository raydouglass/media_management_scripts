import os
import sys
import logging
import subprocess
from media_management_scripts.utils import sizeof_fmt
from media_management_scripts.support.encoding import DEFAULT_PRESET, DEFAULT_CRF, Resolution
from media_management_scripts.utils import create_metadata_extractor

from io import StringIO
from texttable import Texttable

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("convert.log"),
                              logging.StreamHandler()]
                    )
logger = logging.getLogger(__name__)
exe_logger = logging.getLogger('executable-logger')
ffmpeg_exe = '/usr/local/bin/ffmpeg'
nice_exe = '/usr/bin/nice'

DEBUG_MODE = False


def execute(args):
    if nice_exe:
        a = [nice_exe]
        a.extend(args)
        args = a
    logger.debug('Executing: {}'.format(args))
    print(args)
    if DEBUG_MODE:
        print('Debug mod enabled, skipping actual execution')
        return 0
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = StringIO()
    while p.poll() is None:
        l = p.stdout.read(1)  # This blocks until it receives a newline.
        try:
            l = l.decode('utf-8')
            print(l, end='')
            output.write(l)
        except Exception as ex:
            print(ex)
            output.write(str(ex))
    l = p.stdout.read()
    if l:
        try:
            l = l.decode("utf-8")
            print(l)
            output.write(l)
        except Exception as ex:
            print(ex)
            output.write(str(ex))
    exe_logger.debug(output.getvalue())
    output.close()
    return p.poll()


def check_exists(output):
    if os.path.exists(output):
        logger.warning('Cowardly refusing to overwrite existing file: {}'.format(output))
        return True
    return False


def convert(input, output, crf=DEFAULT_CRF, preset=DEFAULT_PRESET, bitrate=None, include_meta=True):
    if check_exists(output):
        return -1
    # ffmpeg -i in -c:v libx264 -crf 15 -preset ultrafast -c:a aac -c:s copy -map 0 out
    metadata = create_metadata_extractor().extract(input)
    if metadata.resolution not in (Resolution.STANDARD_DEF, Resolution.MEDIUM_DEF, Resolution.HIGH_DEF):
        print('{}: Resolution not supported for conversion: {}'.format(input, metadata.resolution))
        # TODO Handle converting 4k content in H.265/HVEC
        return -2
    args = [ffmpeg_exe, '-i', input]
    args.extend(['-c:v', 'libx264'])
    if bitrate:
        crf = 1
        # -x264-params vbv-maxrate=1666:vbv-bufsize=3332:crf-max=22:qpmax=34
        if bitrate == 'auto':
            bitrate = metadata.resolution.auto_bitrate()
        params = 'vbv-maxrate={}:vbv-bufsize={}:crf-max=25:qpmax=34'.format(str(bitrate), str(bitrate * 2))
        args.extend(['-x264-params', params])
    args.extend(['-crf', str(crf), '-preset', preset])
    args.extend(['-c:a', 'aac'])
    args.extend(['-c:s', 'copy'])
    args.extend(['-map', '0'])
    if include_meta:
        args.extend(['-metadata', 'ripped=true'])
        args.extend(['-metadata:s:v:0', 'ripped=true'])
    args.append(output)

    return execute(args)


def combine(video, srt, output, lang=None, convert=False, crf=DEFAULT_CRF, preset=DEFAULT_PRESET):
    if check_exists(output):
        return -1
    create_dirs(output)
    args = [ffmpeg_exe, '-i', video]
    args.extend(['-i', srt])
    if convert:
        args.extend(['-c:v', 'libx264', '-crf', str(crf), '-preset', preset])
        args.extend(['-c:a', 'aac'])
    else:
        args.extend(['-c:v', 'copy'])
        args.extend(['-c:a', 'copy'])
    args.extend(['-c:s', 'copy', '-map', '1:0'])
    # -metadata:s:s:0 language=eng
    if lang:
        args.extend(['-metadata:s:s:0', 'language=' + lang])
    args.extend(['-map', '0'])
    args.append(output)
    return execute(args)


def cut(input, output, start=None, end=None):
    if check_exists(output):
        return -1
    create_dirs(output)
    args = [ffmpeg_exe, '-i', input]
    args.extend(['-c:v', 'copy'])
    args.extend(['-c:a', 'copy'])
    args.extend(['-c:s', 'copy'])
    args.extend(['-map', '0'])
    if start:
        args.extend(['-ss', start])
    if end:
        args.extend(['-to', end])
    args.append(output)
    return execute(args)


def create_dirs(file):
    dir = os.path.dirname(file)
    os.makedirs(dir, exist_ok=True)


def list_files(input_dir):
    for root, subdirs, files in os.walk(input_dir):
        for file in files:
            if not file.startswith('.') and file.endswith('.mkv'):
                path = os.path.join(root, file).replace(input_dir, '')
                yield path


def get_input_output(input_dir, output_dir):
    for file in sorted(list_files(input_dir)):
        input_file = os.path.join(input_dir, file)
        output_file = os.path.join(output_dir, file)
        yield input_file, output_file


def main(input_dir, output_dir, crf=DEFAULT_CRF, preset=DEFAULT_PRESET, bitrate=None):
    files = list(get_input_output(input_dir, output_dir))
    logger.info('{} files to process'.format(len(files)))
    did_process = True
    while did_process:
        did_process = False
        for input_file, output_file in files:
            if not os.path.exists(output_file):
                try:
                    logger.info('Starting convert of {} -> {}'.format(input_file, output_file))
                    create_dirs(output_file)
                    ret = convert(input_file, output_file, crf, preset, bitrate=bitrate, include_meta=True)
                    if ret == 0:
                        did_process = True
                    else:
                        logger.error('Nonzero return code from ffmpeg: {}'.format(ret))

                except Exception as e:
                    logger.exception('Exception during convert')


def _f_percent(per):
    return '{:.2f}%'.format(per)


def do_compare(input, output):
    count = 0
    sum_percent = 0
    bigger = []
    not_converted = []
    table = [['File', 'Original', 'Transcoded', 'Percent']]
    total_i = 0
    total_o = 0
    for i, o in get_input_output(input, output):
        name = os.path.basename(i)
        if os.path.exists(o):
            i_size = os.path.getsize(i)
            o_size = os.path.getsize(o)
            percent = o_size / float(i_size) * 100
            if percent < 15:
                not_converted.append('{} (Too small, {:2f}%)'.format(name, percent))
            elif o_size > i_size:
                bigger.append((name, o, i_size, o_size, percent))
            else:
                count += 1
                total_i += i_size
                total_o += o_size
                sum_percent += percent
                table.append([name, sizeof_fmt(i_size), sizeof_fmt(o_size), _f_percent(percent)])
        else:
            not_converted.append(name)

    if count > 0:
        table.append(['', '', '', ''])
        per = total_o / float(total_i) * 100
        table.append(['Total', sizeof_fmt(total_i), sizeof_fmt(total_o), _f_percent(per)])

        avg = sum_percent / count
        table.append(['Average', '', '', _f_percent(avg)])

    t = Texttable(max_width=0)
    t.set_deco(Texttable.VLINES | Texttable.HEADER)
    t.set_cols_align(['l', 'r', 'r', 'r'])
    t.add_rows(table)

    print(t.draw())

    print('{} Larger than original'.format(len(bigger)))
    for i, o, i_size, o_size, percent in bigger:
        print('{}: {} -> {} ({:.2f}%)'.format(i, sizeof_fmt(i_size), sizeof_fmt(o_size),
                                              percent))
    if len(not_converted) > 0:
        print('Not Converted:')
        for i in not_converted:
            print('  {}'.format(i))
