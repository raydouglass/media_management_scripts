import sys
import os
import re
import shutil

from tempita import Template

season_pattern = re.compile('Season (\d+)')

class RegexResults(object):
    def __init__(self, values=[], ignore_missing=False):
        self.values = values
        self.ignore_missing = ignore_missing

    def __iter__(self):
        return self.values

    def __getitem__(self, index):
        if index < 0 or index >= len(self.values):
            if self.ignore_missing:
                return None
            else:
                raise IndexError('Index out of bounds: {}'.format(index))
        else:
            return self.values[index]


def zpad(s, length=2):
    return str(s).rjust(length, '0')


def lpad(s, length=2):
    return str(s).rjust(length, ' ')


def ifempty(check, if_not_none, if_none=None):
    if if_none is None:
        return check if check is not None else if_not_none
    elif check is None:
        return if_not_none
    else:
        return if_none


RENAMER_NAMESPACE = {
    'lpad': lpad,
    'zpad': zpad,
    'ifempty': ifempty,
    'lower': lambda s: s.lower(),
    'upper': lambda s: s.upper(),
}


def rename_process(template, files, index_start=1, output_dir=None, regex=None, ignore_missing_regex=False, params={}):
    if regex:
        regex = re.compile(regex)

    t = Template(content=template, delimiters=('${', '}'), namespace=RENAMER_NAMESPACE)

    results = []

    index = index_start
    for file in files:
        if output_dir:
            dir = output_dir
        else:
            dir = os.path.dirname(file)
        ext = os.path.splitext(file)[1][1::]
        wo_ext = os.path.splitext(file)[0]
        base = os.path.basename(file)
        new_params = {
            'index': index,
            'i': index,
            'wo_ext': wo_ext,
            'ext': ext,
            'filename': base,
            're': RegexResults(ignore_missing=ignore_missing_regex)
        }
        new_params.update(params)
        if regex:
            m = regex.search(base)
            if m:
                items = [m.group()]
                m_index = 1
                for item in m.groups():
                    try:
                        item = int(item)
                    except ValueError:
                        pass
                    items.append(item)
                    m_index += 1
                    new_params['re'] = new_params['regex'] = RegexResults(items, ignore_missing=ignore_missing_regex)
        result = t.substitute(new_params)
        result = os.path.join(dir, result)
        results.append((file, result))
        index += 1

    return results
