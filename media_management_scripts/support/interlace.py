from media_management_scripts.support.executables import ffmpeg
from media_management_scripts.support.executables import execute_with_output
from typing import NamedTuple
from collections import namedtuple
import re

REPORT_PATTERN = re.compile(
    r"(Single|Multi)[\w\s]+: TFF:\s+(\d+) BFF:\s+(\d+) Progressive:\s+(\d+) Undetermined:\s+(\d+)"
)


# [Parsed_idet_0 @ 0x7f86dfc07f00] Repeated Fields: Neither:    81 Top:     0 Bottom:     0
# [Parsed_idet_0 @ 0x7f86dfc07f00] Single frame detection: TFF:     0 BFF:     0 Progressive:    31 Undetermined:    50
# [Parsed_idet_0 @ 0x7f86dfc07f00] Multi frame detection: TFF:     0 BFF:     0 Progressive:    34 Undetermined:    47


class InterlaceGroup(
    namedtuple("InterlaceGroupBase", ["tff", "bff", "progressive", "undetermined"])
):
    @property
    def ratio(self):
        if self.total_frames:
            return self.interlaced / self.total_frames
        else:
            return 0

    @property
    def interlaced(self):
        return self.tff + self.bff

    @property
    def total_frames(self):
        return self.tff + self.bff + self.progressive + self.undetermined

    def is_undetermined(self, threshold=0.5):
        if self.total_frames:
            return self.undetermined / self.total_frames >= threshold
        else:
            return True

    def is_interlaced(self, threshold=0.5):
        return self.ratio >= threshold

    def combine(self, other):
        return InterlaceGroup(
            tff=self.tff + other.tff,
            bff=self.bff + other.bff,
            progressive=self.progressive + other.progressive,
            undetermined=self.undetermined + other.undetermined,
        )

    def to_dict(self):
        return {
            "tff": self.tff,
            "bff": self.bff,
            "progressive": self.progressive,
            "undetermined": self.undetermined,
            "total_frames": self.total_frames,
        }


class InterlaceReport(namedtuple("InterlaceReportBase", ["single", "multi"])):
    single: InterlaceGroup
    multi: InterlaceGroup

    @property
    def ratio(self):
        if self.total_frames:
            return self.interlaced / self.total_frames
        else:
            return 0

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

    def is_undetermined(self, threshold=0.5):
        return self.single.is_undetermined(threshold) or self.multi.is_undetermined(
            threshold
        )

    def is_interlaced(self, threshold=0.5):
        return self.ratio >= threshold

    def combine(self, other):
        return InterlaceReport(
            single=self.single.combine(other.single),
            multi=self.multi.combine(other.multi),
        )

    def to_dict(self):
        return {
            "interlaced": self.is_interlaced(),
            "single": self.single.to_dict(),
            "multi": self.single.to_dict(),
        }


def _parse_output(output: str):
    lines = output.splitlines(False)
    lines = lines[-2::]
    single, multi = None, None
    for line in lines:
        m = REPORT_PATTERN.search(line)
        if m:
            if m.group(1) == "Single":
                single = InterlaceGroup(
                    int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
                )
            else:
                multi = InterlaceGroup(
                    int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
                )
        else:
            raise Exception("Not matched: {}".format(line))
    return InterlaceReport(single, multi)


def _execute_ffmpeg(input_file: str, frames: int, start: int = 0):
    args = [
        ffmpeg(),
        "-ss",
        str(start),
        "-i",
        input_file,
        "-filter:v",
        "idet",
        "-frames:v",
        str(frames),
        "-an",
        "-f",
        "rawvideo",
        "-y",
        "/dev/null",
    ]
    ret, output = execute_with_output(args, print_output=False)
    if ret != 0:
        raise Exception(
            "Non-zero ffmpeg return code: {}. Output={}".format(ret, output)
        )
    return _parse_output(output)


def _find_interlace(
    input_file: str,
    frames: int = 100,
    max_frames: int = 6400,
    undetermined_threshold: float = 0.5,
    metadata=None,
) -> InterlaceReport:
    if frames > max_frames:
        return None
    # ffmpeg -filter:v idet -frames:v 100 -an -f rawvideo -y /dev/null -i
    if metadata and metadata.estimated_duration and metadata.estimated_duration < 200:
        start = 0
    else:
        # Skip the first three minutes as this is usually commercials or introduction
        start = 180
    report = _execute_ffmpeg(input_file, frames, start=start)
    if metadata and metadata.estimated_duration:
        midpoint = int(metadata.estimated_duration / 2)
        report2 = _execute_ffmpeg(input_file, frames, start=midpoint)
        report = report.combine(report2)
    if report.is_undetermined(undetermined_threshold):
        new_report = _find_interlace(
            input_file, frames * 2, max_frames, undetermined_threshold, metadata
        )
        if new_report:
            return new_report
    return report


def find_interlace(
    input_file: str,
    frames: int = 100,
    max_frames: int = 6400,
    undetermined_threshold: float = 0.33,
    metadata=None,
) -> InterlaceReport:
    if frames > max_frames:
        raise Exception("Frames cannot be larger than max")
    return _find_interlace(
        input_file, frames, max_frames, undetermined_threshold, metadata
    )
