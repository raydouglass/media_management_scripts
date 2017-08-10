import os
import subprocess
import tempfile
from media_management_scripts.support.executables import ffmpeg


def _temp_convert(input, output):
    # ffmpeg -i input1.mp4 -c copy -bsf:v h264_mp4toannexb -f mpegts intermediate1.ts
    print('Converting {}'.format(input))
    p = subprocess.Popen(
        [ffmpeg(), '-loglevel', 'fatal', '-i', input, '-c', 'copy', '-bsf:v', 'h264_mp4toannexb', '-f', 'mpegts',
         output], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    p.wait()
    if stderr:
        raise Exception(stderr)


def _concat(files, output):
    # ffmpeg -i "concat:intermediate1.ts|intermediate2.ts" -c copy -bsf:a aac_adtstoasc output.mp4
    concat_str = 'concat:'
    for f in files:
        concat_str += f + '|'
    concat_str = concat_str[0:-1]
    print(concat_str)
    p = subprocess.Popen(
        [ffmpeg(), '-loglevel', 'fatal', '-y', '-i', concat_str, '-c', 'copy', '-bsf:a', 'aac_adtstoasc',
         output],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    p.wait()
    if stderr:
        raise Exception(stderr)


def concat_mp4(output, files, overwrite=False):
    if not overwrite and os.path.exists(output):
        print('Cowardly refusing to overwrite existing file: {}'.format(output))
        return
    temp_files = []
    for f in files:
        file = os.path.abspath(f)
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.ts').name
        temp_files.append(tmp)
        _temp_convert(file, tmp)
    _concat(temp_files, output)
    for f in temp_files:
        os.remove(f)
