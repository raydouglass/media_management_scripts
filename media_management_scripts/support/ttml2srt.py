# This file modified from https://github.com/codingcatgirl/ttml2srt
# License of that repo below:
# MIT License
#
# Copyright (c) 2017 Laura Klunder
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re
import sys
from datetime import timedelta
from xml.etree import ElementTree as ET


def format_timestamp(timestamp: timedelta):
    return (
        "%02d:%02d:%02.3f"
        % (
            timestamp.total_seconds() // 3600,
            timestamp.total_seconds() // 60 % 60,
            timestamp.total_seconds() % 60,
        )
    ).replace(".", ",")


# parse correct start and end times
def parse_time_expression(
    expression, default_offset=timedelta(0), frame_rate: int = None
):
    offset_time = re.match(r"^([0-9]+(\.[0-9]+)?)(h|m|s|ms|f|t)$", expression)
    if offset_time:
        time_value, fraction, metric = offset_time.groups()
        time_value = float(time_value)
        if metric == "h":
            return default_offset + timedelta(hours=time_value)
        elif metric == "m":
            return default_offset + timedelta(minutes=time_value)
        elif metric == "s":
            return default_offset + timedelta(seconds=time_value)
        elif metric == "ms":
            return default_offset + timedelta(milliseconds=time_value)
        elif metric == "f":
            raise NotImplementedError(
                "Parsing time expressions by frame is not supported!"
            )
        elif metric == "t":
            raise NotImplementedError(
                "Parsing time expressions by ticks is not supported!"
            )

    clock_time = re.match(
        r"^([0-9]{2,}):([0-9]{2,}):([0-9]{2,}(\.[0-9]+)?)$", expression
    )
    if clock_time:
        hours, minutes, seconds, fraction = clock_time.groups()
        return timedelta(hours=int(hours), minutes=int(minutes), seconds=float(seconds))

    clock_time_frames = re.match(
        r"^([0-9]{2,}):([0-9]{2,}):([0-9]{2,}):([0-9]{2,}(\.[0-9]+)?)$", expression
    )
    if clock_time_frames and not frame_rate:
        raise NotImplementedError(
            "Parsing time expressions by frame is not supported! No frame_rate provided."
        )
    elif clock_time_frames:
        hours, minutes, seconds, fraction, _ = clock_time_frames.groups()
        seconds = float(seconds) + int(fraction) / frame_rate
        return timedelta(hours=int(hours), minutes=int(minutes), seconds=seconds)

    raise ValueError("unknown time expression: %s" % expression)


def parse_times(elem, default_begin=timedelta(0), frame_rate: int = None):
    if "begin" in elem.attrib:
        begin = parse_time_expression(
            elem.attrib["begin"], default_offset=default_begin, frame_rate=frame_rate
        )
    else:
        begin = default_begin
    elem.attrib["{abs}begin"] = begin

    end = None
    if "end" in elem.attrib:
        end = parse_time_expression(
            elem.attrib["end"], default_offset=default_begin, frame_rate=frame_rate
        )

    dur = None
    if "dur" in elem.attrib:
        dur = parse_time_expression(elem.attrib["dur"], frame_rate=frame_rate)

    if dur is not None:
        if end is None:
            end = begin + dur
        else:
            end = min(end, begin + dur)

    elem.attrib["{abs}end"] = end

    for child in elem:
        parse_times(child, default_begin=begin, frame_rate=frame_rate)


# render subtitles on each timestamp
def render_subtitles(elem, timestamp, styles, parent_style={}):
    if timestamp < elem.attrib["{abs}begin"]:
        return ""
    if elem.attrib["{abs}end"] is not None and timestamp >= elem.attrib["{abs}end"]:
        return ""

    result = ""

    style = parent_style.copy()
    if "style" in elem.attrib:
        style.update(styles.get(elem.attrib["style"], {}))

    if "color" in style:
        result += '<font color="%s">' % style["color"]

    is_italic = False
    if (
        style.get("fontstyle") == "italic"
        or elem.attrib.get("fontStyle", None) == "italic"
    ):
        result += " <i>"
        is_italic = True

    if elem.text:
        result += elem.text.strip()
    if len(elem):
        for child in elem:
            result += render_subtitles(child, timestamp, styles)
            if child.tail:
                result += child.tail.strip()

    result = result.rstrip()
    if is_italic:
        result += "</i> "

    if "color" in style:
        result += "</font>"

    if elem.tag in ("div", "p", "br"):
        result += "\n"

    return result


def convert_to_srt(srt_file: str, output_file: str = None):
    tree = ET.parse(srt_file)
    root = tree.getroot()

    # strip namespaces
    for elem in root.getiterator():
        elem.tag = elem.tag.split("}", 1)[-1]
        elem.attrib = {
            name.split("}", 1)[-1]: value for name, value in elem.attrib.items()
        }

    # get styles
    styles = {}
    for elem in root.findall("./head/styling/style"):
        style = {}
        if "color" in elem.attrib:
            color = elem.attrib["color"]
            if color not in ("#FFFFFF", "#000000"):
                style["color"] = color
        if "fontStyle" in elem.attrib:
            fontstyle = elem.attrib["fontStyle"]
            if fontstyle in ("italic",):
                style["fontstyle"] = fontstyle
        styles[elem.attrib["id"]] = style

    body = root.find("./body")

    frame_rate = root.attrib.get("frameRate", None)
    if frame_rate:
        frame_rate = int(frame_rate)

    parse_times(body, frame_rate=frame_rate)

    timestamps = set()
    for elem in body.findall(".//*[@{abs}begin]"):
        timestamps.add(elem.attrib["{abs}begin"])

    for elem in body.findall(".//*[@{abs}end]"):
        timestamps.add(elem.attrib["{abs}end"])

    timestamps.discard(None)

    rendered = []
    for timestamp in sorted(timestamps):
        rendered.append(
            (
                timestamp,
                re.sub(
                    r"\n\n\n+", "\n\n", render_subtitles(body, timestamp, styles)
                ).strip(),
            )
        )

    if not rendered:
        exit(0)

    # group timestamps together if nothing changes
    rendered_grouped = []
    last_text = None
    for timestamp, content in rendered:
        if content != last_text:
            rendered_grouped.append((timestamp, content))
        last_text = content

    # output srt
    # rendered_grouped.append((rendered_grouped[-1][0] + timedelta(hours=24), ''))

    with open(output_file, "w") if output_file else sys.stdout as f:
        srt_i = 1
        for i, (timestamp, content) in enumerate(rendered_grouped[:-1]):
            if content == "":
                continue
            content = content.strip()
            print(str(srt_i), file=f)
            print(
                format_timestamp(timestamp)
                + " --> "
                + format_timestamp(rendered_grouped[i + 1][0]),
                file=f,
            )
            print(content, file=f)
            srt_i += 1
            print("", file=f)
