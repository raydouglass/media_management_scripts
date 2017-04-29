from media_management_scripts.support.executables import ffmpeg
from media_management_scripts.support.executables import execute_with_output
from typing import NamedTuple
from collections import namedtuple
import re

REPORT_PATTERN = re.compile(
    '(Single|Multi)[\w\s]+: TFF:\s+(\d+) BFF:\s+(\d+) Progressive:\s+(\d+) Undetermined:\s+(\d+)')


# [Parsed_idet_0 @ 0x7f86dfc07f00] Repeated Fields: Neither:    81 Top:     0 Bottom:     0
# [Parsed_idet_0 @ 0x7f86dfc07f00] Single frame detection: TFF:     0 BFF:     0 Progressive:    31 Undetermined:    50
# [Parsed_idet_0 @ 0x7f86dfc07f00] Multi frame detection: TFF:     0 BFF:     0 Progressive:    34 Undetermined:    47

class InterlaceGroup(namedtuple('InterlaceGroupBase', ['tff', 'bff', 'progressive', 'undetermined'])):
    @property
    def ratio(self):
        return self.interlaced / self.total_frames

    @property
    def interlaced(self):
        return self.tff + self.bff

    @property
    def total_frames(self):
        return self.tff + self.bff + self.progressive + self.undetermined

    def is_interlaced(self, threshold=.5):
        return self.ratio >= threshold


class InterlaceReport(namedtuple('InterlaceReportBase', ['single', 'multi'])):
    single: InterlaceGroup
    multi: InterlaceGroup

    @property
    def ratio(self):
        return self.interlaced / self.total_frames

    @property
    def interlaced(self):
        return self.single.interlaced + self.multi.interlaced

    @property
    def undetermined(self):
        return self.single.undetermined + self.multi.undetermined

    @property
    def progressive(self):
        return self.single.progressive + self.multi.progressive

    @property
    def total_frames(self):
        return self.single.total_frames + self.multi.total_frames

    def is_interlaced(self, threshold=.5):
        return self.ratio >= threshold


def find_interlace(input_file: str, frames: int = 100) -> InterlaceReport:
    # fmpeg -filter:v idet -frames:v 100 -an -f rawvideo -y /dev/null -i
    args = [ffmpeg(), '-filter:v', 'idet', '-frames:v', str(frames), '-an', '-f', 'rawvideo', '-y', '/dev/null', '-i',
            input_file]
    ret, output = execute_with_output(args, print_output=False)
    if ret != 0:
        raise Exception()
    lines = output.splitlines(False)
    lines = lines[-2::]
    single, multi = None, None
    for line in lines:
        m = REPORT_PATTERN.search(line)
        if m:
            if m.group(1) == 'Single':
                single = InterlaceGroup(int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)))
            else:
                multi = InterlaceGroup(int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)))
        else:
            raise Exception('Not matched: {}'.format(line))
    return InterlaceReport(single, multi)
