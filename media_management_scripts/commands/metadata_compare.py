from . import SubCommand
from .common import *
import os


def create_table_object(input_to_cmd, interlace="none"):
    from media_management_scripts.utils import create_metadata_extractor
    from media_management_scripts.support.formatting import sizeof_fmt, duration_to_str

    extractor = create_metadata_extractor()
    metadatas = [extractor.extract(i, interlace != "none") for i in input_to_cmd]
    header = [""] + [os.path.basename(f.file) for f in metadatas]
    num_audio = max([len(m.audio_streams) for m in metadatas])
    rows = ["Size", "Duration", "Bitrate (kb/s)", "Video Codec", "Resolution", "Audio"]
    for i in range(1, num_audio):
        rows.append("")
    rows.append("Subtitles")
    file_columns = [rows]
    first_size = os.path.getsize(metadatas[0].file)
    for m in metadatas:
        data = []
        size = os.path.getsize(m.file)
        size_ratio = "{:.1f}%".format(size / first_size * 100)
        data.append("{} ({})".format(sizeof_fmt(size), size_ratio))
        data.append(
            duration_to_str(m.estimated_duration) if m.estimated_duration else ""
        )
        data.append("{:.2f}".format(m.bit_rate / 1024.0))
        video = m.video_streams[0]
        data.append(video.codec)
        data.append("{}x{}".format(video.width, video.height))
        for a in m.audio_streams:
            data.append("{} ({}, {})".format(a.codec, a.language, a.channel_layout))
        for i in range(len(m.audio_streams), num_audio):
            data.append("")
        data.append(",".join([s.language for s in m.subtitle_streams]))
        file_columns.append(data)
    table = list(map(list, zip(*file_columns)))
    return header, table


class MetadataCompareCommand(SubCommand):
    @property
    def name(self):
        return "compare"

    def build_argparse(self, subparser):
        metadata_parser = subparser.add_parser(
            self.name, help="Compare metadata between files", parents=[parent_parser]
        )
        metadata_parser.add_argument(
            "--interlace",
            help="Try to detect interlacing",
            choices=["none", "summary", "report"],
            default="none",
        )
        metadata_parser.add_argument("input", nargs="+")

    def subexecute(self, ns):
        input_to_cmd = ns["input"]
        interlace = ns["interlace"]
        header, table = create_table_object(input_to_cmd, interlace)
        self._bulk_print(table, header)


SubCommand.register(MetadataCompareCommand)


class CompareDirectoryCommand(SubCommand):
    @property
    def name(self):
        return "compare-directory"

    def build_argparse(self, subparser):
        parser = subparser.add_parser(
            self.name, help="Show metadata for a file", parents=[parent_parser]
        )
        parser.add_argument("source")
        parser.add_argument("destination")
        parser.add_argument("--db", help="Metadata temp DB")

    def subexecute(self, ns):
        from media_management_scripts.utils import create_metadata_extractor
        from media_management_scripts.support.files import get_input_output, list_files
        from media_management_scripts.support.formatting import bitrate_to_str

        src_dir = ns["source"]
        dst_dir = ns["destination"]
        dst_files = list(list_files(dst_dir))
        meta_db = ns.get("db", None)

        table = []
        extractor = create_metadata_extractor(meta_db)
        for src_file, dst_file in get_input_output(src_dir, dst_dir):
            row = []
            src_meta = extractor.extract(src_file)
            src_video = src_meta.video_streams[0]

            row.append(os.path.basename(src_file))
            row.append(src_video.codec)
            row.append("{}x{}".format(src_video.width, src_video.height))
            row.append(bitrate_to_str(src_meta.bit_rate))
            # row.append(dst_file)

            if os.path.exists(dst_file):
                dst_meta = extractor.extract(dst_file)
                dst_video = dst_meta.video_streams[0]
                row.append(dst_video.codec)
                row.append("{}x{}".format(dst_video.width, dst_video.height))
                row.append(bitrate_to_str(dst_meta.bit_rate))
            else:
                row.append("")
                row.append("")
                row.append("")
            table.append(tuple(row))

        columns = [
            "Source",
            "Src Codec",
            "Src Resolution",
            "Src Bitrate",  #'Destination',
            "Dest Codec",
            "Dest Resolution",
            "Dest Bitrate",
        ]
        self._bulk_print(table, columns)


SubCommand.register(CompareDirectoryCommand)
