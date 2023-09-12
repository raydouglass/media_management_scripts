from abc import ABCMeta, abstractmethod
import shutil
from typing import List, Tuple, Callable
from media_management_scripts.support.files import check_exists, create_dirs


class SubCommand(metaclass=ABCMeta):
    def __init__(self):
        self.dry_run = False
        self.ns = None

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def build_argparse(self, subparser):
        raise Exception("Not implemented")

    @abstractmethod
    def subexecute(self, ns):
        raise Exception("Not implemented")

    def execute(self, ns):
        self.dry_run = ns["dry_run"]
        self.ns = ns
        self.subexecute(ns)

    def _move(self, src, dst, overwrite=False):
        if self.dry_run:
            print("Move: {}=>{}".format(src, dst))
        else:
            if not overwrite and check_exists(dst, log=self.dry_run):
                return False
            create_dirs(dst)
            shutil.move(src, dst)
            return True

    def _copy(self, src, dst, overwrite=False):
        if self.dry_run:
            print("Copy: {}=>{}".format(src, dst))
        else:
            if not overwrite and check_exists(dst, log=self.dry_run):
                return False
            create_dirs(dst)
            shutil.copy(src, dst)
            return True

    def _bulk(
        self,
        files: List[Tuple[str, ...]],
        op: Callable[[str, str], None],
        column_descriptions: List[str] = [],
        src_index=0,
        dest_index=1,
        print_table=True,
    ):
        from texttable import Texttable

        if not print_table and self.dry_run:
            return
        if print_table:
            table = [column_descriptions]
            table.extend(files)
            t = Texttable(max_width=0)
            t.set_deco(Texttable.VLINES | Texttable.HEADER | Texttable.BORDER)
            t.add_rows(table)
            print(t.draw())
        if not self.dry_run:
            for file_tuple in files:
                src = file_tuple[src_index]
                dst = file_tuple[dest_index]
                if src and dst:
                    op(src, dst)

    def _bulk_move(
        self,
        files: List[Tuple[str, ...]],
        column_descriptions: List[str] = [],
        src_index=0,
        dest_index=1,
        print_table=True,
    ):
        """
        Moves/Renames multiple files
        :param files: a list of tuples containing the source file, destination file, and any other information to display
        :param column_descriptions: a list of the description for each column in the file list tuple
        :param src_index: which index of the tuple is the source file
        :param dest_index: which index of the tuple is the destination file
        :return:
        """
        self._bulk(
            files,
            op=self._move,
            column_descriptions=column_descriptions,
            src_index=src_index,
            dest_index=dest_index,
            print_table=print_table,
        )

    def _bulk_copy(
        self,
        files: List[Tuple[str, ...]],
        column_descriptions: List[str] = [],
        src_index=0,
        dest_index=1,
        print_table=True,
    ):
        """
        Copies multiple files
         :param files: a list of tuples containing the source file, destination file, and any other information to display
         :param column_descriptions: a list of the description for each column in the file list tuple
         :param src_index: which index of the tuple is the source file
         :param dest_index: which index of the tuple is the destination file
         :return:
        """
        self._bulk(
            files,
            op=self._copy,
            column_descriptions=column_descriptions,
            src_index=src_index,
            dest_index=dest_index,
            print_table=print_table,
        )

    def _bulk_print(
        self,
        files: List[Tuple[str, ...]],
        column_descriptions: List[str] = [],
        src_index=0,
        dest_index=1,
    ):
        self._bulk(
            files,
            op=lambda x, y: None,
            column_descriptions=column_descriptions,
            src_index=src_index,
            dest_index=dest_index,
            print_table=True,
        )


__all__ = [
    "SubCommand",
    "combine_subtitles",
    #'compare_directories',
    "concat_mp4",
    "convert",
    "executables",
    "find_episodes",
    "itunes",
    "metadata",
    "metadata_compare",
    "movie_rename",
    "rename",
    "search",
    "select_streams",
    #'split',
    "subtitles",
    "thumbnail",
    "tv_rename",
]
