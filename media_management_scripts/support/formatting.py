def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def duration_to_str(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return '%dh%02dm%02ds' % (h, m, s)
    else:
        return '%02dm%02ds' % (m, s)


def bitrate_to_str(bitrate: float):
    if bitrate is None:
        return None
    bitrate = float(bitrate)
    if bitrate < 1024:
        return '{:.2f} b/s'.format(bitrate)
    bitrate /= 1024
    if bitrate < 10 * 1024:  # 10 MB
        return '{:.0f} Kbps'.format(bitrate)
    else:
        bitrate /= 1024
        return '{:.2f} Mbps'.format(bitrate)
