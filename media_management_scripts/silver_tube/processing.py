import xml.etree.ElementTree as ET
from media_management_scripts.utils import create_metadata_extractor, convert_config_from_config_section
from media_management_scripts.silver_tube.wtv import extract_original_air_date
from media_management_scripts import tvdb_api
from media_management_scripts.silver_tube.wtv_db import WtvDb
from media_management_scripts.convert import convert_with_config
from media_management_scripts.support.episode_finder import extract as extract_season_ep
from media_management_scripts.support.executables import ccextractor, comskip
import os
import subprocess
import logging
import logging.config
import pysrt
from copy import copy
import configparser
import datetime
import glob
from string import Template
from typing import Tuple, List

from media_management_scripts.support.executables import execute_with_output, ffmpeg, execute_with_timeout, nice_exe
from media_management_scripts.renamer import create_namespace
from tempita import Template

logger = logging.getLogger(__name__)
exe_logger = logging.getLogger('executable-logger')


class Configuration():
    def __init__(self, config_file, tvdb):
        config = configparser.ConfigParser()
        config.read(config_file)
        log_file = config.get('main', 'log.config', fallback=None)
        if log_file:
            import yaml
            with open(log_file) as f:
                log_config = yaml.load(f)
                logging.config.dictConfig(log_config)

        template = config.get('directories', 'out.pattern',
                              fallback='${series}/Season ${season}/${series} - S${season|zpad}E${episode|zpad} - ${episode_name}.${ext}')
        self.template = template

        self.wtv_in_dir = config.get('directories', 'tv.in')
        self.tv_pattern = config.get('directories', 'tv.pattern')
        self.com_in_dir = config.get('directories', 'commercial.in')
        self.srt_in_dir = config.get('directories', 'srt.in')
        self.temp_dir = config.get('directories', 'temp.dir')
        self.out_dir = config.get('directories', 'out.dir')
        self.delete_source = config.getboolean('directories', 'delete.source.files', fallback=True)

        self.convert_config = convert_config_from_config_section(config, 'transcode')

        if config.has_section('ffmpeg'):
            logger.error('You are using an outdated configuration')
            raise Exception('You are using an outdated configuration')

        self.debug = config.getboolean('main', 'debug', fallback=False)

        self.ccextractor_exe = config.get('ccextractor', 'executable', fallback=ccextractor())
        self.ccextractor_run = config.getboolean('ccextractor', 'run.if.missing', fallback=False)

        self.comskip_exe = config.get('comskip', 'executable', fallback=None)
        self.comskip_run = config.getboolean('comskip', 'run.if.missing', fallback=comskip())
        self.comskip_ini = config.get('comskip', 'comskip.ini', fallback=None)

        db_file = config.get('main', 'database.file', fallback='db.sqlite')

        self.wtvdb = WtvDb(db_file)
        self.tvdb = tvdb

        if self.convert_config.include_subtitles:
            logger.warning('Include Subtitles is True. This usually does not work with TV captions.')

    def get_metadata(self, wtv_file: str) -> Tuple[str, str, int, int]:
        # Will detect deinterlace if we actually have to process this file
        metadata = create_metadata_extractor().extract(wtv_file, detect_interlace=False)
        series = metadata.tags.get('Title', None)
        episode_name = metadata.tags.get('WM/SubTitle', None)
        # WM/SubTitleDescription

        filename = os.path.basename(wtv_file)
        wtv_obj = self.wtvdb.get_wtv(filename)
        if wtv_obj and wtv_obj.selected_episode:
            ep = wtv_obj.selected_episode.episode
            season = ep.season
            episode_num = ep.episode_num
            if episode_name is None:
                episode_name = ep.name
        elif series is not None:
            # Get season & episode number
            air_date = extract_original_air_date(wtv_file, parse_from_filename=True, metadata=metadata)
            episodes = self.tvdb.find_episode(series, episode=episode_name, air_date=air_date)
            if len(episodes) == 1:
                season, episode_num = tvdb_api.TVDB.season_number(episodes[0])
                if episodes[0]['episodeName'] is not None:
                    episode_name = episodes[0]['episodeName']
            else:
                # Handle multiple options
                self.wtvdb.store_candidates(self.tvdb, filename, metadata, episodes)
                season = None
                episode_num = None
        else:
            season = None
            episode_num = None

        # Try searching the description
        if season is None and episode_num is None and 'WM/SubTitleDescription' in metadata.tags:
            season, episode_num, _ = extract_season_ep(metadata.tags['WM/SubTitleDescription'])

        if episode_name is None and episode_num is not None:
            episode_name = 'Episode #{}'.format(episode_num)

        return series, episode_name, season, episode_num, metadata

    def process(self, wtv_file: str, com_file: str, srt_file: str):
        # Ensure TVDB client is authenticated
        self.tvdb.refresh()

        series, episode_name, season, episode_num, metadata = self.get_metadata(wtv_file)
        if series is not None and season is not None and episode_num is not None:
            # Detect interlace
            create_metadata_extractor().add_interlace_report(metadata)
            filename = os.path.basename(wtv_file)
            filename_wo_ext = os.path.splitext(filename)[0]
            out_video = os.path.join(self.out_dir,
                                     create_filename(self.template, series, season, episode_num, episode_name,
                                                     filename_wo_ext, 'mp4'))
            out_srt = os.path.join(self.out_dir,
                                   create_filename(self.template, series, season, episode_num, episode_name,
                                                   filename_wo_ext,
                                                   'eng.srt'))

            if not os.path.exists(os.path.dirname(out_video)):
                os.makedirs(os.path.dirname(out_video))
            if not os.path.exists(os.path.dirname(out_srt)):
                os.makedirs(os.path.dirname(out_srt))

            commercials = parse_commercial_file(com_file)
            split_subtitles(srt_file, invert_commercial(commercials), out_srt)
            successful = self.convert(wtv_file, out_video, commercials, metadata)
            if successful:
                # If we finished with the WTV, delete it
                if self.wtvdb.get_wtv(filename) is not None:
                    self.wtvdb.delete_wtv(filename)
                if not self.debug and self.delete_source:
                    os.remove(wtv_file)
                    os.remove(com_file)
                    os.remove(srt_file)
                logger.info('Completed {} => {}'.format(wtv_file, out_video))
            else:
                logger.warning('Failure to convert {}'.format(wtv_file))
        else:
            logger.warning(
                'Missing data for {}: series={}, episode_name={}, season={}, episode_num={}'.format(wtv_file, series,
                                                                                                    episode_name,
                                                                                                    season,
                                                                                                    episode_num))

    def extract_subtitles(self, wtv_file, out_srt):
        execute_with_output([self.ccextractor_exe, wtv_file, '-o', out_srt])

    def run_comskip(self, wtv_file, out_dir):
        try:
            if self.comskip_ini:
                ret, stdout = execute_with_timeout(
                    [self.comskip_exe, '--ini=' + self.comskip_ini, '--output=' + out_dir, wtv_file],
                    timeout=60 * 10)
            else:
                ret, stdout = execute_with_timeout([self.comskip_exe, '--output=' + out_dir, wtv_file], timeout=60 * 10,
                                                   log_output=True)
            if ret != 0:
                logger.error('Comskip error: {}, Output={}'.format(ret, stdout))
                return False
            else:
                return True
        except subprocess.TimeoutExpired:
            return False

    def cut_args(self, invert_com, out_name):
        # -ss 0 -t 10 -c:v libx264 -preset ultrafast -crf 18 -c:a aac -strict -2 0.mp4
        args = ['-ss', str(invert_com[0])]
        if invert_com[1]:
            args.extend(['-to', str(invert_com[1])])
        args.extend(['-c:v', 'copy', '-c:a', 'copy'])
        args.append(out_name)
        return args

    def convert(self, in_file, out_file, commercials, metadata):
        invert = invert_commercial(commercials)
        temp_files = []
        wo_ext = os.path.basename(in_file).replace('.wtv', '')
        try:
            args = [ffmpeg(), '-i', in_file]
            for i in invert:
                temp_file = os.path.join(self.temp_dir, wo_ext + '.' + str(len(temp_files)) + '.ts')
                temp_files.append(temp_file)
                if os.path.isfile(temp_file):
                    os.remove(temp_file)
                args.extend(self.cut_args(i, temp_file))

            ret, output = execute_with_output(args)
            if ret != 0:
                logger.error('Nonzero return code from ffmpeg: {}'.format(ret))
                return False
            else:
                input = 'concat:{}'.format('|'.join(temp_files))
                ret = convert_with_config(input, out_file, config=self.convert_config, print_output=False,
                                          overwrite=True, metadata=metadata)
                if ret != 0:
                    logger.error('Nonzero return code from ffmpeg: {}'.format(ret))
                # Cleanup temp files
                if not self.debug:
                    for f in temp_files:
                        os.remove(f)
        except Exception as e:
            logger.exception('Exception')
            return False
        return True

    def run(self):
        wtv_dir, com_dir, srt_dir = self.wtv_in_dir, self.com_in_dir, self.srt_in_dir
        self.count = 0
        files = glob.glob(os.path.join(wtv_dir, self.tv_pattern))
        for wtv_file in sorted(files):
            if os.path.isfile(wtv_file):
                self.wtvdb.begin()
                try:
                    # wtv_file = os.path.join(wtv_dir, wtv)
                    wtv = os.path.basename(wtv_file)
                    time = datetime.datetime.now() - datetime.timedelta(minutes=5)
                    modified = datetime.datetime.fromtimestamp(os.path.getmtime(wtv_file))
                    if modified < time:
                        com = wtv.replace('wtv', 'xml')
                        srt = wtv.replace('wtv', 'srt')
                        com_file = os.path.join(com_dir, com)
                        srt_file = os.path.join(srt_dir, srt)
                        if not os.path.isfile(com_file) and self.comskip_run:
                            logger.debug('No commercial file for {}. Running comskip'.format(wtv_file))
                            if not self.run_comskip(wtv_file, com_dir):
                                logger.error('Comskip error or timed out for: {}'.format(wtv_file))
                                continue
                        if not os.path.isfile(srt_file) and self.ccextractor_run:
                            logger.debug('No srt file for {}. Running ccextractor'.format(wtv_file))
                            self.extract_subtitles(wtv_file, srt_file)
                        if os.path.isfile(com_file) and os.path.isfile(srt_file):
                            logger.info('Processing {}'.format(wtv_file))
                            self.process(wtv_file, com_file, srt_file)
                            self.count += 1
                        elif not os.path.isfile(com_file):
                            logger.warning('No commercial file for {}...skipping'.format(wtv_file))
                        else:
                            logger.warning('No srt file for {}...skipping'.format(wtv_file))
                    else:
                        logger.debug('File too new, skipping: {}'.format(wtv))
                except Exception:
                    logger.exception('Exception while handling {}'.format(wtv))
                    self.wtvdb.end()
        logger.info('Processed {} files'.format(self.count))


def parse_commercial_file(com_file) -> List[Tuple[float, float]]:
    tree = ET.parse(com_file)
    root = tree.getroot()
    commercials = []
    for child in root:
        commercials.append((float(child.get('start')), float(child.get('end'))))
    return commercials


def invert_commercial(commercials):
    inverse = [(0, commercials[0][0])]
    for i in range(len(commercials) - 1):
        left = commercials[i]
        right = commercials[i + 1]
        inverse.append((left[1], right[0]))
    if len(commercials) > 1:
        inverse.append((commercials[len(commercials) - 1][1], None))
    return inverse


def to_time(c):
    c = float(c)
    hours = int(c / (60 * 60))
    minutes = int(c / 60)
    if c >= 0:
        seconds = int(c % 60)
    else:
        seconds = -int(-c % 60)
    milliseconds = int((c - int(c)) * 1000)
    return {'hours': hours, 'minutes': minutes, 'seconds': seconds, 'milliseconds': milliseconds}


def split_subtitles(srt_file, invert_commercials, out_file):
    subs = pysrt.open(srt_file)
    parts = []
    prev = 0.0
    shift = 0
    for c in invert_commercials:
        shift = shift - float(c[0]) + prev
        s = []
        for i in subs.data:
            if i.start >= to_time(c[0]) and (c[1] is None or i.start < to_time(c[1])):
                temp = copy(i)
                time = to_time(shift)
                temp.shift(hours=time['hours'], minutes=time['minutes'], seconds=time['seconds'],
                           milliseconds=time['milliseconds'])
                parts.append(temp)
            else:
                pass
            prev = c[1] if c[1] is not None else -1
    subs = pysrt.SubRipFile(items=parts)
    subs.save(out_file)


def durations_to_invert(durations):
    ret = []
    pos = 0
    for i in durations:
        ret.append((pos, pos + i))
        pos = pos + i
    return ret


def create_filename(template, series, season, episode_num, episode_name, filename, extension):
    t = Template(content=template, delimiters=('${', '}'), namespace=create_namespace())
    d = dict(
        series=series,
        season=season,
        episode=episode_num,
        episode_name=episode_name,
        ext=extension,
        orig_basename=filename
    )
    return t.substitute(d)
