from . import SubCommand
from .common import *
from .metadata_compare import create_table_object


class CompareDirectoriesCommand(SubCommand):
    @property
    def name(self):
        return "compare-directories"

    def build_argparse(self, subparser):
        combine_video_subtitles_parser = subparser.add_parser(
            self.name, help="", parents=[parent_parser]
        )
        combine_video_subtitles_parser.add_argument("source", help="")
        combine_video_subtitles_parser.add_argument("destination", help="")

    def get_table(self, header, data):
        from texttable import Texttable

        table = [header]
        table.extend(data)
        t = Texttable(max_width=0)
        t.set_deco(Texttable.VLINES | Texttable.HEADER | Texttable.BORDER)
        t.add_rows(table)
        return t.draw()

    def should_replace(self):
        pass

    def subexecute(self, ns):
        source = ns["source"]
        destination = ns["destination"]
        from media_management_scripts.support.files import list_files
        from dialog import Dialog
        import os

        source_files = sorted(list_files(source))
        destination_files = set(list_files(destination))

        files_to_copy = []

        for source_file in source_files:
            if source_file not in destination_files:
                files_to_copy.append(source_file)
            else:
                src_path = os.path.join(source, source_file)
                dst_path = os.path.join(destination, source_file)

                header, data = create_table_object([src_path, dst_path])
                table_str = self.get_table(header, data)
                table_str += "\n\nOverwrite?"

                result = Dialog(autowidgetsize=True).yesno(text=table_str)
                if result == "ok":
                    files_to_copy.append(source_file)

        for file in files_to_copy:
            print(file)
