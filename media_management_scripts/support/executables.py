from io import StringIO
import logging
import subprocess
import re
from typing import Tuple, Callable, List, NamedTuple


def ffmpeg():
    return '/usr/local/bin/ffmpeg'


def ffprobe():
    return '/usr/local/bin/ffprobe'


def comskip():
    return '/usr/local/bin/comskip'


def ccextractor():
    return '/usr/local/bin/ccextractor'


exe_logger = logging.getLogger('executable-logger')
nice_exe = '/usr/bin/nice'

DEBUG_MODE = False
logger = logging.getLogger(__name__)


class FFMpegProgress(NamedTuple):
    """
    Represents the periodic output of FFMPEG as a key-value store:
    frame=  128 fps= 85 q=28.0 size=      27kB time=00:00:05.66 bitrate=  39.1kbits/s speed=3.77x
    """
    frame: int
    fps: int
    q: float
    size: int
    time: str
    bitrate: str
    speed: float
    percent: int
    remaining_time: float

    @property
    def time_as_seconds(self):
        v = self.time.split(':')
        return float(v[0]) * 60 * 60 + float(v[1]) * 60 + float(v[2])

    def progress(self, duration: float):
        return self.time // duration

    def remaining_time(self, duration: float):
        speed = float(self.speed[:-1])
        return (duration - self.time) / speed


def create_ffmpeg_callback(cb: Callable[[FFMpegProgress], None]) -> Callable[[str], None]:
    """
    Converts a callback function that accepts a FFMpegProgress to one that accepts a str for use in execute_with_callback
    :param cb:
    :return:
    """
    pattern = re.compile('(\w+)=\s*([\w:/\.]+)')

    def wrapper(line):
        values = {}
        for m in pattern.finditer(line):
            key = m.group(1)
            value = m.group(2).lstrip()
            values[key] = value
        if 'time' in values:
            progress = FFMpegProgress(**values)
            cb(progress)

    return wrapper


def execute_with_timeout(args, timeout: int, use_nice=True, log_output=False) -> Tuple[int, str]:
    if use_nice:
        a = [nice_exe]
        a.extend(args)
        args = a
    logger.debug('Executing: {}'.format(args))
    with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
        stdout, stderr = p.communicate()
        if stdout and log_output:
            exe_logger.info(stdout)
        if stderr and log_output:
            exe_logger.error(stderr)
        try:
            return p.wait(timeout=timeout), stdout
        except subprocess.TimeoutExpired as e:
            p.kill()
            p.communicate()
            raise e


def execute_with_output(args, print_output=False, use_nice=True) -> Tuple[int, str]:
    if use_nice and nice_exe:
        a = [nice_exe]
        a.extend(args)
        args = a
    logger.debug('Executing: {}'.format(args))
    if print_output:
        print('Executing: {}'.format(' '.join([str(a) for a in args])))
    if DEBUG_MODE:
        logger.debug('Debug mod enabled, skipping actual execution')
        return 0
    with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as p:
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
        output.close()
        if print_output:
            exe_logger.debug(result)
        output.close()
        return p.poll(), result


def execute_with_callback(args: List[str], callback: Callable[[str], None], use_nice: bool = True) -> int:
    if use_nice and nice_exe:
        a = [nice_exe]
        a.extend(args)
        args = a
    logger.debug('Executing: {}'.format(args))
    with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as p:
        output = StringIO()

        while p.poll() is None:
            try:
                l = p.stdout.read(1)
            except IOError:
                continue
            try:
                if l:
                    l = l.decode('utf-8')
                    if l == '\n' or l == '\r':
                        callback(output.getvalue())
                        output = StringIO()
                    else:
                        output.write(l)
            except Exception as ex:
                raise ex
        l = p.stdout.read()
        if l:
            try:
                l = l.decode('utf-8')
                callback(l)
            except Exception as ex:
                raise ex
        return p.poll()
