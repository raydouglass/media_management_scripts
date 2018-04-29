import os
import subprocess
import tempfile
from media_management_scripts.support.executables import ffmpeg, execute_with_output


def _temp_convert(input, output, print_output=False):
    # ffmpeg -i input1.mp4 -c copy -bsf:v h264_mp4toannexb -f mpegts intermediate1.ts
    print('Converting {}'.format(input))
    args = [ffmpeg(),
            '-loglevel', 'fatal',
            '-i', input,
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-c:s', 'copy',
            '-bsf:v', 'h264_mp4toannexb',
            '-f', 'mpegts',
            output]
    ret, r = execute_with_output(args, print_output=print_output)
    if ret != 0:
        raise Exception('Error during ffmpeg: {}'.format(r))


def _concat(files, output, print_output=False):
    # ffmpeg -i "concat:intermediate1.ts|intermediate2.ts" -c copy -bsf:a aac_adtstoasc output.mp4
    concat_str = 'concat:'
    for f in files:
        concat_str += f + '|'
    concat_str = concat_str[0:-1]
    print(concat_str)
    args = [ffmpeg(),
            '-loglevel', 'fatal',
            '-y',
            '-i', concat_str,
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-c:s', 'copy',
            '-bsf:a', 'aac_adtstoasc',
            output]
    ret, r = execute_with_output(args, print_output=print_output)
    if ret != 0:
        raise Exception('Error during ffmpeg: {}'.format(r))


def concat_mp4(output, files, overwrite=False, print_output=False):
    if not overwrite and os.path.exists(output):
        print('Cowardly refusing to overwrite existing file: {}'.format(output))
        return
    temp_files = []
    try:
        for f in files:
            file = os.path.abspath(f)
            tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.ts').name
            temp_files.append(tmp)
            _temp_convert(file, tmp, print_output)
        _concat(temp_files, output, print_output)
    finally:
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)
