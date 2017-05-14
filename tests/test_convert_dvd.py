from tests import create_test_video, VideoDefinition
from media_management_scripts.support.encoding import VideoFileContainer
import unittest
from tempfile import TemporaryDirectory, NamedTemporaryFile
import configparser


# [directories]
# movie.dir.in = /mnt/media/Convert/Movie
# tv.dir.in = /mnt/media/Convert/TV Shows
# working.dir = /mnt/media/Working
# movie.dir.out = /mnt/media/
# tv.dir.out = /mnt/media/
#
# [backup]
# rclone = /usr/local/bin/rclone
# split = /usr/local/bin/gsplit
# backup.path = dest:/path/to/dest
# max.size = 25
# split.size = 5G
#
# [transcode]
# bitrate = auto
# crf = 18
# preset = veryfast
# deinterlace = True
# deinterlace_threshold = .5
#
# [logging]
# level = DEBUG
# file = convert.log
# db = processed.shelve


class ConvertDvdTestCase(unittest.TestCase):
    def test_movie(self):
        temporary_dirs = []
        temporary_files = []
        try:
            config_file = NamedTemporaryFile(suffix='ini')
            config_parser = configparser.ConfigParser()

            movie_dir_in = TemporaryDirectory()
            config_parser['directories']['movie.dir.in']

        finally:
            for temp in temporary_dirs:
                if temp:
                    temp.cleanup()
            for temp in temporary_files:
                if temp:
                    temp.close()
