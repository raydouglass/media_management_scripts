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