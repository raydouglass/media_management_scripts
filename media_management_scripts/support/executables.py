from io import StringIO
import logging
import subprocess
import re
from typing import Tuple, Callable, List, NamedTuple

import configparser
import os
import shutil

ffmpeg_exe = shutil.which("ffmpeg")
ffprobe_exe = shutil.which("ffprobe")
comskip_exe = shutil.which("comskip")
ccextractor_exe = shutil.which("ccextractor")
nice_exe = shutil.which("nice")
java_exe = shutil.which("java")
filebot_jar_loc = None

config_file = os.path.expanduser("~/.config/mms/executables.ini")
if os.path.exists(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    ffmpeg_exe = config.get("main", "ffmpeg", fallback=ffmpeg_exe)
    ffprobe_exe = config.get("main", "ffprobe", fallback=ffprobe_exe)
    comskip_exe = config.get("main", "comskip", fallback=comskip_exe)
    ccextractor_exe = config.get("main", "ccextractor", fallback=ccextractor_exe)
    nice_exe = config.get("main", "nice", fallback=nice_exe)
    java_exe = config.get("main", "java", fallback=java_exe)
    filebot_jar_loc = config.get("main", "filebot_jar", fallback=filebot_jar_loc)


class ExecutableNotFoundException(Exception):
    pass


def ffmpeg():
    if ffmpeg_exe is None:
        raise ExecutableNotFoundException("ffmpeg executable was not found.")
    return ffmpeg_exe


def ffprobe():
    if ffprobe_exe is None:
        raise ExecutableNotFoundException("ffprobe executable was not found.")
    return ffprobe_exe


def comskip():
    if comskip_exe is None:
        raise ExecutableNotFoundException("comskip executable was not found.")
    return comskip_exe


def ccextractor():
    if ccextractor_exe is None:
        raise ExecutableNotFoundException("ccextractor executable was not found.")
    return ccextractor_exe


def java():
    if java_exe is None:
        raise ExecutableNotFoundException("java executable was not found.")
    return java_exe


def filebot_jar():
    if filebot_jar_loc is None:
        raise ExecutableNotFoundException("filebot jar was not found.")
    return filebot_jar_loc


EXECUTABLES = [ffmpeg, ffprobe, comskip, ccextractor, java, filebot_jar]


exe_logger = logging.getLogger("executable-logger")

DEBUG_MODE = False
logger = logging.getLogger(__name__)


class FFMpegProgress(NamedTuple):
    """
    Represents the periodic output of FFMPEG as a key-value store:
    frame=  128 fps= 85 q=28.0 size=      27kB time=00:00:05.66 bitrate=  39.1kbits/s speed=3.77x
    """

    time: str
    bitrate: str
    speed: str

    @property
    def time_as_seconds(self):
        try:
            v = self.time.split(":")
            return float(v[0]) * 60 * 60 + float(v[1]) * 60 + float(v[2])
        except ValueError:
            return None

    def progress(self, duration: float):
        return self.time_as_seconds / duration if self.time_as_seconds else None

    def remaining_time(self, duration: float):
        try:
            speed = float(self.speed[:-1])
            return (duration - self.time_as_seconds) / speed
        except ValueError:
            return None


def create_ffmpeg_callback(
    cb: Callable[[FFMpegProgress], None]
) -> Callable[[str], None]:
    """
    Converts a callback function that accepts a FFMpegProgress to one that accepts a str for use in execute_with_callback
    :param cb:
    :return:
    """
    pattern = re.compile(r"(\w+)=\s*([-\w:/\.]+)")

    def wrapper(line):
        values = {}
        for m in pattern.finditer(line):
            key = m.group(1)
            value = m.group(2).lstrip()
            values[key] = value
        if "time" in values and "bitrate" in values and "speed" in values:
            progress = FFMpegProgress(
                values["time"], values["bitrate"], values["speed"]
            )
            cb(progress)

    return wrapper


def execute_with_timeout(
    args, timeout: int, use_nice=True, log_output=False
) -> Tuple[int, str]:
    if use_nice:
        a = [nice_exe]
        a.extend(args)
        args = a
    logger.debug("Executing: {}".format(args))
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
    logger.debug("Executing: {}".format(args))
    if print_output:
        print("Executing: {}".format(" ".join([str(a) for a in args])))
    if DEBUG_MODE:
        logger.debug("Debug mod enabled, skipping actual execution")
        return 0
    with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as p:
        output = StringIO()
        while p.poll() is None:
            l = p.stdout.read(1)
            try:
                l = l.decode("utf-8")
                if print_output:
                    print(l, end="")
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


def execute_with_callback(
    args: List[str], callback: Callable[[str], None], use_nice: bool = True
) -> int:
    if use_nice and nice_exe:
        a = [nice_exe]
        a.extend(args)
        args = a
    logger.debug("Executing: {}".format(args))
    with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as p:
        output = StringIO()

        while p.poll() is None:
            try:
                l = p.stdout.read(1)
            except IOError:
                continue
            try:
                if l:
                    l = l.decode("utf-8", errors="ignore")
                    if l == "\n" or l == "\r":
                        callback(output.getvalue())
                        output = StringIO()
                    else:
                        output.write(l)
            except Exception as ex:
                p.kill()
                raise ex
        l = p.stdout.read()
        if l:
            try:
                l = l.decode("utf-8")
                callback(l)
            except Exception as ex:
                p.kill()
                raise ex
        return p.poll()


def execute_ffmpeg_with_dialog(args, duration: float = None, title=None, text=None):
    from media_management_scripts.support.formatting import duration_to_str

    if ffmpeg() not in args:
        raise Exception("Execute ffmpeg called without ffmpeg args")
    from dialog import Dialog

    d = Dialog(autowidgetsize=False)
    d.gauge_start(
        title=title, text=text if text else "", percent=0 if duration else None
    )

    def cb(ffmpeg_progress: FFMpegProgress):
        if duration:
            remaining = ffmpeg_progress.remaining_time(duration)
            if remaining:
                remaining_time = duration_to_str(remaining)
                d.gauge_update(
                    percent=int(ffmpeg_progress.progress(duration) * 100),
                    text="Remaining: {}".format(remaining_time),
                    update_text=True,
                )

    try:
        callback = create_ffmpeg_callback(cb)
        return execute_with_callback(args, callback)
    finally:
        d.gauge_stop()
