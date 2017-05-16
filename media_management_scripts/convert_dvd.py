import os
import logging
from media_management_scripts.utils import sizeof_fmt
from media_management_scripts.support.encoding import DEFAULT_PRESET, DEFAULT_CRF, Resolution, H264Preset
from media_management_scripts.utils import create_metadata_extractor
from typing import NamedTuple
from texttable import Texttable
from media_management_scripts.support.executables import execute_with_output, ffmpeg

logger = logging.getLogger(__name__)


class ConvertConfig(NamedTuple):
    crf: int = DEFAULT_CRF
    preset: str = DEFAULT_PRESET
    bitrate: str = None
    include_meta: bool = False
    deinterlace: bool = False
    deinterlace_threshold: float = .5


def convert_config_from_ns(ns):
    vars = {}
    for field in ConvertConfig._fields:
        value = ns.get(field, ConvertConfig._field_defaults.get(field, None))
        vars[field] = value
    return ConvertConfig(**vars)


def execute(args, print_output=True):
    ret, _ = execute_with_output(args, print_output)
    return ret


def check_exists(output):
    if os.path.exists(output):
        logger.warning('Cowardly refusing to overwrite existing file: {}'.format(output))
        return True
    return False


def convert_with_config(input, output, config, print_output=True, overwrite=False):
    if not overwrite and check_exists(output):
        return -1
    if print_output:
        print('Converting {} -> {}'.format(input, output))
        print('Using config: {}'.format(config))
    # ffmpeg -i in -c:v libx264 -crf 15 -preset ultrafast -c:a aac -c:s copy -map 0 out
    metadata = create_metadata_extractor().extract(input, detect_interlace=config.deinterlace)
    if metadata.resolution not in (Resolution.STANDARD_DEF, Resolution.MEDIUM_DEF, Resolution.HIGH_DEF):
        print('{}: Resolution not supported for conversion: {}'.format(input, metadata.resolution))
        # TODO Handle converting 4k content in H.265/HVEC
        return -2
    args = [ffmpeg()]
    if overwrite:
        args.append('-y')
    args.extend(['-i', input])

    args.extend(['-c:v', 'libx264'])
    crf = config.crf
    bitrate = config.bitrate
    if config.bitrate:
        crf = 1
        # -x264-params vbv-maxrate=1666:vbv-bufsize=3332:crf-max=22:qpmax=34
        if config.bitrate == 'auto':
            bitrate = metadata.resolution.auto_bitrate
        params = 'vbv-maxrate={}:vbv-bufsize={}:crf-max=25:qpmax=34'.format(str(bitrate), str(bitrate * 2))
        args.extend(['-x264-params', params])
    args.extend(['-crf', str(crf), '-preset', config.preset])
    if config.deinterlace:
        is_interlaced = metadata.interlace_report.is_interlaced(config.deinterlace_threshold)
        if print_output:
            print('{} - Interlaced: {}'.format(metadata.interlace_report, is_interlaced))
        if is_interlaced:
            # Video is interlaced, so add the deinterlace filter
            args.extend(['-vf', 'yadif'])
    args.extend(['-c:a', 'aac'])
    index = 0
    for audio in metadata.audio_streams:
        if audio.channels == 7:
            # 6.1 sound, so mix it up to 7.1
            args.extend(['-ac:a:{}'.format(index), '8'])
        index += 1
    args.extend(['-c:s', 'copy'])
    args.extend(['-map', '0'])
    if config.include_meta:
        args.extend(['-metadata', 'ripped=true'])
        args.extend(['-metadata:s:v:0', 'ripped=true'])
    args.append(output)

    return execute(args, print_output)


def convert(input, output, crf=DEFAULT_CRF, preset=DEFAULT_PRESET, bitrate=None, include_meta=True, print_output=True):
    config = ConvertConfig(crf=crf, preset=preset, bitrate=bitrate, include_meta=include_meta)
    return convert_with_config(input, output, config, print_output)


def combine(video, srt, output, lang=None, convert=False, crf=DEFAULT_CRF, preset=DEFAULT_PRESET):
    if check_exists(output):
        return -1
    create_dirs(output)
    args = [ffmpeg(), '-i', video]
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
    args = [ffmpeg(), '-i', input]
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
    if dir:
        os.makedirs(dir, exist_ok=True)


def list_files(input_dir):
    for root, subdirs, files in os.walk(input_dir):
        for file in files:
            if not file.startswith('.') and file.endswith('.mkv'):
                path = os.path.join(root, file).replace(input_dir, '')
                if path.startswith('/'):
                    path = path[1::]
                yield path


def get_input_output(input_dir, output_dir, work_dir=None):
    for file in sorted(list_files(input_dir)):
        input_file = os.path.join(input_dir, file)
        output_file = os.path.join(output_dir, file)
        if work_dir:
            work_file = os.path.join(work_dir, file)
            yield input_file, output_file, work_file
        else:
            yield input_file, output_file


def main(input_dir, output_dir, config):
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
                    ret = convert_with_config(input_file, output_file, config, include_meta=True)
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
