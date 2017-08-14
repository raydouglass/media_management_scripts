from abc import ABCMeta, abstractmethod
import shutil


class SubCommand(metaclass=ABCMeta):
    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def build_argparse(self, subparser):
        raise Exception('Not implemented')

    @abstractmethod
    def subexecute(self, ns):
        raise Exception('Not implemented')

    def execute(self, ns):
        self.dry_run = ns['dry_run']
        self.subexecute(ns)

    def _move(self, src, dst):
        if self.dry_run:
            print('Move: {}=>{}'.format(src, dst))
        else:
            shutil.move(src, dst)

    def _copy(self, src, dst):
        if self.dry_run:
            print('Copy: {}=>{}'.format(src, dst))
        else:
            shutil.copy(src, dst)


__all__ = ['SubCommand',
           'combine_subtitles',
           'concat_mp4',
           'convert',
           'find_episodes',
           'itunes',
           'metadata',
           'movie_rename',
           'rename',
           'search',
           'select_streams',
           'split',
           'strip_youtube_dl',
           'tv_rename']
