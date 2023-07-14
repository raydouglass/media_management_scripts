import re

DURATION_PATTERN = re.compile(r"-?(((\d+(\.\d+)?)h)?(\d+(\.\d+)?)m)?(\d+(\.\d+)?)s")


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Yi", suffix)


def duration_to_str(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return "%dh%02dm%02ds" % (h, m, s)
    else:
        return "%02dm%02ds" % (m, s)


def duration_from_str(dur_str):
    """
    Converts a string in 00h00m00.00s to seconds
    :param dur_str:
    :return:
    """
    m = DURATION_PATTERN.match(dur_str)
    if m:
        hours = m.group(3)
        minutes = m.group(5)
        seconds = m.group(7)
        hours = float(hours) * 60 * 60 if hours else 0
        minutes = float(minutes) * 60 if minutes else 0
        total = hours + minutes + float(seconds)
        if dur_str.startswith("-"):
            total *= -1
        return total
    else:
        raise Exception("Invalid duration format: " + dur_str)


def bitrate_to_str(bitrate: float):
    if bitrate is None:
        return None
    bitrate = float(bitrate)
    if bitrate < 1024:
        return "{:.2f} b/s".format(bitrate)
    bitrate /= 1024
    if bitrate < 10 * 1024:  # 10 MB
        return "{:.0f} Kbps".format(bitrate)
    else:
        bitrate /= 1024
        return "{:.2f} Mbps".format(bitrate)
