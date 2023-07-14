import logging
import os
from typing import List

from texttable import Texttable

from media_management_scripts.support.encoding import (
    DEFAULT_PRESET,
    DEFAULT_CRF,
    Resolution,
    resolution_name,
    VideoCodec,
    AudioCodec,
)
from media_management_scripts.support.executables import (
    execute_with_output,
    ffmpeg,
    nice_exe,
)
from media_management_scripts.support.files import (
    check_exists,
    create_dirs,
    get_input_output,
)
from media_management_scripts.support.formatting import sizeof_fmt
from media_management_scripts.utils import (
    create_metadata_extractor,
    ConvertConfig,
    extract_metadata,
)
from media_management_scripts.support.ttml2srt import convert_to_srt

logger = logging.getLogger(__name__)


def convert_config_from_ns(ns):
    vars = {}
    for field in ConvertConfig._fields:
        value = ns.get(field, ConvertConfig._field_defaults.get(field, None))
        vars[field] = value
    return ConvertConfig(**vars)


def execute(args, print_output=True):
    ret, r = execute_with_output(args, print_output)
    return ret


def auto_bitrate_from_config(resolution, convert_config):
    if convert_config.scale:
        resolution = resolution_name(convert_config.scale)
    if resolution == Resolution.LOW_DEF:
        return convert_config.auto_bitrate_240
    elif resolution == Resolution.STANDARD_DEF:
        return convert_config.auto_bitrate_480
    elif resolution == Resolution.MEDIUM_DEF:
        return convert_config.auto_bitrate_720
    elif resolution == Resolution.HIGH_DEF:
        return convert_config.auto_bitrate_1080
    else:
        raise Exception("Not auto bitrate for {}".format(resolution))


def convert_with_config(
    input,
    output,
    config: ConvertConfig,
    print_output=True,
    overwrite=False,
    metadata=None,
    mappings=None,
    use_nice=True,
):
    """

    :param input:
    :param output:
    :param config:
    :param print_output:
    :param overwrite:
    :param metadata:
    :param mappings: List of mappings (for example ['0:0', '0:1'])
    :return:
    """
    if not overwrite and check_exists(output):
        return -1
    if print_output:
        print("Converting {} -> {}".format(input, output))
        print("Using config: {}".format(config))

    if not metadata:
        metadata = create_metadata_extractor().extract(
            input, detect_interlace=config.deinterlace
        )
    elif config.deinterlace and not metadata.interlace_report:
        raise Exception(
            "Metadata provided without interlace report, but convert requires deinterlace checks"
        )

    if (
        metadata.resolution
        not in (
            Resolution.LOW_DEF,
            Resolution.STANDARD_DEF,
            Resolution.MEDIUM_DEF,
            Resolution.HIGH_DEF,
        )
        and not config.scale
    ):
        print(
            "{}: Resolution not supported for conversion: {}".format(
                input, metadata.resolution
            )
        )
        # TODO Handle converting 4k content in H.265/HVEC
        return -2
    if use_nice and nice_exe:
        args = [nice_exe, ffmpeg()]
    else:
        args = [ffmpeg()]
    if overwrite:
        args.append("-y")
    if config.start:
        args.extend(["-ss", str(config.start)])
    if config.end:
        if config.end > 0:
            args.extend(["-to", str(config.end)])
        else:
            new_end = metadata.estimated_duration + config.end
            args.extend(["-to", str(new_end)])

    args.extend(["-i", input])

    if config.scale:
        args.extend(["-vf", "scale=-1:{}".format(config.scale)])

    args.extend(["-c:v", config.video_codec])
    crf = config.crf
    bitrate = config.bitrate
    if (
        VideoCodec.H264.equals(config.video_codec)
        and config.bitrate is not None
        and config.bitrate != "disabled"
    ):
        crf = 1
        # -x264-params vbv-maxrate=1666:vbv-bufsize=3332:crf-max=22:qpmax=34
        if config.bitrate == "auto":
            bitrate = auto_bitrate_from_config(metadata.resolution, config)
        params = "vbv-maxrate={}:vbv-bufsize={}:crf-max=25:qpmax=34".format(
            str(bitrate), str(bitrate * 2)
        )
        args.extend(["-x264-params", params])
    elif (
        VideoCodec.H265.equals(config.video_codec)
        and config.bitrate is not None
        and config.bitrate != "disabled"
    ):
        raise Exception("Avg Bitrate not supported for H265")

    args.extend(["-crf", str(crf), "-preset", config.preset])
    if config.deinterlace:
        is_interlaced = metadata.interlace_report.is_interlaced(
            config.deinterlace_threshold
        )
        if print_output:
            print(
                "{} - Interlaced: {}".format(metadata.interlace_report, is_interlaced)
            )
        if is_interlaced:
            # Video is interlaced, so add the deinterlace filter
            args.extend(["-vf", "yadif"])

    args.extend(["-c:a", config.audio_codec])

    index = 0
    for audio in metadata.audio_streams:
        if audio.channels == 7:
            # 6.1 sound, so mix it up to 7.1
            args.extend(["-ac:a:{}".format(index), "8"])
        index += 1

    if config.include_subtitles:
        args.extend(["-c:s", "copy"])

    if not mappings:
        args.extend(["-map", "0"])
    else:
        for m in mappings:
            if type(m) == int:
                args.extend(["-map", "0:{}".format(m)])
            else:
                args.extend(["-map", m])

    if config.include_meta:
        args.extend(["-metadata", "ripped=true"])
        args.extend(["-metadata:s:v:0", "ripped=true"])
    args.append(output)

    return execute(args, print_output)


def create_remux_args(
    input_files: List[str],
    output_file: str,
    mappings: List,
    overwrite=False,
    metadata={},
):
    """

    :param input_files:
    :param output_file:
    :param mappings:
    :param overwrite:
    :param metadata: {'s:0': {'language':'eng'}, '': {'title': 'A Great Movie'}}
    :return:
    """
    if not overwrite and check_exists(output_file):
        return -1
    args = [ffmpeg()]
    if overwrite:
        args.append("-y")
    for input_file in input_files:
        args.extend(["-i", input_file])
    args.extend(["-c", "copy"])
    for m in mappings:
        if type(m) == int:
            args.extend(["-map", "0:{}".format(m)])
        else:
            args.extend(["-map", m])
    for key, value in metadata.items():
        if key:
            key = ":s:" + key
        for meta_key, meta_val in value.items():
            args.append("-metadata{}".format(key))
            args.append("{}={}".format(meta_key, meta_val))

    args.append(output_file)
    return args


def convert(
    input,
    output,
    crf=DEFAULT_CRF,
    preset=DEFAULT_PRESET,
    bitrate=None,
    include_meta=True,
    print_output=True,
):
    config = ConvertConfig(
        crf=crf, preset=preset, bitrate=bitrate, include_meta=include_meta
    )
    return convert_with_config(input, output, config, print_output)


def combine(
    video,
    srt,
    output,
    lang=None,
    overwrite=False,
    convert=False,
    crf=DEFAULT_CRF,
    preset=DEFAULT_PRESET,
    skip_eia_608=True,
):
    if not overwrite and check_exists(output):
        return -1

    if srt.endswith(".ttml") or srt.endswith(".xml"):
        logger.debug("Converting ttml/xml to srt")
        name, _ = os.path.splitext(srt)
        srt_out = name + ".srt"
        convert_to_srt(srt, srt_out)
        srt = srt_out
    create_dirs(output)
    args = [ffmpeg(), "-i", video]
    if overwrite:
        args.append("-y")
    args.extend(["-i", srt])
    args.extend(["-map", "0:v", "-map", "0:a"])
    if skip_eia_608:
        metadata = extract_metadata(video)
        for i in (s.index for s in metadata.subtitle_streams if s.codec != "eia_608"):
            args.extend(["-map", "0:{}".format(i)])
    else:
        args.extend(["-map", "0:s?"])
    args.extend(["-map", "1:0"])
    if convert:
        args.extend(["-c:v", "libx264", "-crf", str(crf), "-preset", preset])
        args.extend(["-c:a", "aac"])
    else:
        args.extend(["-c:v", "copy"])
        args.extend(["-c:a", "copy"])
    args.extend(["-c:s", "copy"])
    # -metadata:s:s:0 language=eng
    if lang:
        args.extend(["-metadata:s:s:0", "language=" + lang])
    args.append(output)
    return execute(args)


def cut(input, output, start=None, end=None):
    if check_exists(output):
        return -1
    create_dirs(output)
    args = [ffmpeg(), "-i", input]
    args.extend(["-c:v", "copy"])
    args.extend(["-c:a", "copy"])
    args.extend(["-c:s", "copy"])
    args.extend(["-map", "0"])
    if start:
        args.extend(["-ss", str(start)])
    if end:
        args.extend(["-to", str(end)])
    args.append(output)
    return execute(args)


def main(input_dir, output_dir, config):
    files = list(get_input_output(input_dir, output_dir))
    logger.info("{} files to process".format(len(files)))
    did_process = True
    while did_process:
        did_process = False
        for input_file, output_file in files:
            if not os.path.exists(output_file):
                try:
                    logger.info(
                        "Starting convert of {} -> {}".format(input_file, output_file)
                    )
                    create_dirs(output_file)
                    ret = convert_with_config(input_file, output_file, config)
                    if ret == 0:
                        did_process = True
                    else:
                        logger.error("Nonzero return code from ffmpeg: {}".format(ret))

                except Exception as e:
                    logger.exception("Exception during convert")


def _f_percent(per):
    return "{:.2f}%".format(per)


def do_compare(input, output):
    count = 0
    sum_percent = 0
    bigger = []
    not_converted = []
    table = [["File", "Original", "Transcoded", "Percent"]]
    total_i = 0
    total_o = 0
    for i, o in get_input_output(input, output):
        name = os.path.basename(i)
        if os.path.exists(o):
            i_size = os.path.getsize(i)
            o_size = os.path.getsize(o)
            percent = o_size / float(i_size) * 100
            if percent < 15:
                not_converted.append("{} (Too small, {:2f}%)".format(name, percent))
            elif o_size > i_size:
                bigger.append((name, o, i_size, o_size, percent))
            else:
                count += 1
                total_i += i_size
                total_o += o_size
                sum_percent += percent
                table.append(
                    [name, sizeof_fmt(i_size), sizeof_fmt(o_size), _f_percent(percent)]
                )
        else:
            not_converted.append(name)

    if count > 0:
        table.append(["", "", "", ""])
        per = total_o / float(total_i) * 100
        table.append(
            ["Total", sizeof_fmt(total_i), sizeof_fmt(total_o), _f_percent(per)]
        )

        avg = sum_percent / count
        table.append(["Average", "", "", _f_percent(avg)])

    t = Texttable(max_width=0)
    t.set_deco(Texttable.VLINES | Texttable.HEADER)
    t.set_cols_align(["l", "r", "r", "r"])
    t.add_rows(table)

    print(t.draw())

    print("{} Larger than original".format(len(bigger)))
    for i, o, i_size, o_size, percent in bigger:
        print(
            "{}: {} -> {} ({:.2f}%)".format(
                i, sizeof_fmt(i_size), sizeof_fmt(o_size), percent
            )
        )
    if len(not_converted) > 0:
        print("Not Converted:")
        for i in not_converted:
            print("  {}".format(i))


def _read_file(f):
    with open(f, encoding="utf8", errors="ignore") as file:
        return file.read()


def convert_subtitles_to_srt(i: str, o: str):
    ext = os.path.splitext(i)[1]
    if ext == ".srt":
        import shutil

        shutil.copy(i, o)
    elif ext in (".ttml", ".xml", ".dfxp", ".tt"):
        # TTML
        from media_management_scripts.support.ttml2srt import convert_to_srt

        convert_to_srt(i, o)
    else:
        # VTT, SCC, etc

        from pycaption import detect_format, SRTWriter

        subtitle_str = _read_file(i)
        reader = detect_format(subtitle_str)
        if reader:
            subtitle_str = SRTWriter().write(reader().read(subtitle_str))
            with open(o, "w") as file:
                file.write(subtitle_str)
        else:
            # Attempt to use FFMPEG
            from media_management_scripts.support.executables import ffmpeg
            from media_management_scripts.support.executables import execute_with_output

            args = [ffmpeg(), "-loglevel", "fatal", "-y", "-i", i, "-c:s", "srt", o]
            ret, output = execute_with_output(args)
            if ret != 0:
                raise Exception(
                    "Exception during subtitle conversion: {}".format(output)
                )
