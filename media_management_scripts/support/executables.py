from io import StringIO
import logging
import subprocess


def ffmpeg():
    return '/usr/local/bin/ffmpeg'


def ffprobe():
    return '/usr/local/bin/ffprobe'


exe_logger = logging.getLogger('executable-logger')
ffmpeg_exe = '/usr/local/bin/ffmpeg'
nice_exe = '/usr/bin/nice'

DEBUG_MODE = False
logger = logging.getLogger(__name__)


def execute_with_output(args, print_output=False):
    if nice_exe:
        a = [nice_exe]
        a.extend(args)
        args = a
    logger.debug('Executing: {}'.format(args))
    if print_output:
        print('Executing: {}'.format(' '.join([str(a) for a in args])))
    if DEBUG_MODE:
        logger.debug('Debug mod enabled, skipping actual execution')
        return 0
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = StringIO()
    while p.poll() is None:
        l = p.stdout.read(1)
        try:
            l = l.decode('utf-8')
            if print_output:
                print(l, end='')
            output.write(l)
        except Exception as ex:
            if print_output:
                print(ex)
            output.write(str(ex))
    l = p.stdout.read()
    if l:
        try:
            l = l.decode("utf-8")
            if print_output:
                print(l)
            output.write(l)
        except Exception as ex:
            if print_output:
                print(ex)
            output.write(str(ex))
    result = output.getvalue()
    if print_output:
        exe_logger.debug(result)
    output.close()
    return p.poll(), result
