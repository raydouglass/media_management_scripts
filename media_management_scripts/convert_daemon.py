from media_management_scripts.convert_dvd import get_input_output, create_dirs, execute, convert_with_config, \
    ConvertConfig
from media_management_scripts.support.encoding import DEFAULT_CRF, DEFAULT_PRESET
import logging
import os
import shelve
import re
import subprocess
import math
import shutil
import configparser
import sqlite3
from datetime import datetime, timedelta
from typing import Tuple

logger = logging.getLogger(__name__)

TV_NAME_REGEX = re.compile('.+ - S\d\dE\d\d(-E\d\d)? - .+\.mkv')
MOVIE_NAME_REGEX = re.compile('.+ \(\d{4}\)( - \d+p)?\.mkv')


class ProcessStatus():
    """
    This class tracks the status of an input file whether it was successfully backed up or converted.
    """
    def __init__(self, input_file, output_file, backup=False, convert=False):
        self.input_file = input_file
        self.output_file = output_file
        self.backup = backup
        self.convert = convert

    def should_process(self):
        return not (self.backup and self.convert)

    def __repr__(self):
        return '<ProcessStatus: input={}, output={}, backup={}, convert={}>'.format(self.input_file, self.output_file,
                                                                                    self.backup, self.convert)


class ProcessedDatabase():
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.conn.execute(
            'CREATE TABLE IF NOT EXISTS processed(input PRIMARY KEY, output VARCHAR, backup BOOLEAN, convert BOOLEAN);')
        self.conn.commit()

    def get(self, input_file, output_file):
        logger.debug('Getting: {}'.format(input_file))
        row = self.conn.execute('SELECT backup, convert FROM processed WHERE input = ?', (input_file,)).fetchone()
        if row:
            status = ProcessStatus(input_file, output_file, row[0] == 1, row[1] == 1)
            logger.debug('Found: {}'.format(status))
        else:
            logger.debug('Not found, saving new')
            status = ProcessStatus(input_file, output_file)
            self.save(status)
        return status

    def save(self, status):
        logger.debug('Saving: {}'.format(status))
        self.conn.execute('REPLACE INTO processed (input, output, backup, convert) VALUES (?, ?, ?, ?);',
                          (status.input_file, status.output_file, status.backup, status.convert))
        self.conn.commit()

    def get_all_success(self):
        for row in self.conn.execute('SELECT input, output, backup, convert FROM processed WHERE backup AND convert;'):
            yield ProcessStatus(row[0], row[1], row[2], row[3])

    def get_all_existing_success(self):
        return [status for status in self.get_all_success() if
                os.path.exists(status.input_file) and os.path.exists(status.output_file)]


class ConvertDvds():
    def __init__(self, config_file):
        config = configparser.ConfigParser()
        config.read(config_file)

        # Directories
        self.movie_in_dir = config.get('directories', 'movie.dir.in')
        self.tv_in_dir = config.get('directories', 'tv.dir.in')
        self.working_dir = config.get('directories', 'working.dir')
        self.movie_out_dir = config.get('directories', 'movie.dir.out')
        self.tv_out_dir = config.get('directories', 'tv.dir.out')

        # Backup
        self.rclone_exe = config.get('backup', 'rclone')
        self.split_exe = config.get('backup', 'split')
        self.backup_path = config.get('backup', 'backup.path')
        self.max_size = int(config.get('backup', 'max.size')) * (1024 ** 3)
        self.split_size = config.get('backup', 'split.size')

        # Transcode
        crf = config.get('transcode', 'crf', fallback=DEFAULT_CRF)
        preset = config.get('transcode', 'preset', fallback=DEFAULT_PRESET)
        bitrate = config.get('transcode', 'bitrate', fallback=None)
        deinterlace = config.get('transcode', 'deinterlace', fallback=False)
        deinterlace_threshold = config.get('transcode', 'deinterlace_threshold', fallback=.5)
        self.convert_config = ConvertConfig(crf=crf, preset=preset, bitrate=bitrate, deinterlace=deinterlace,
                                            deinterlace_threshold=deinterlace_threshold, include_meta=True)

        # Logging
        level = config.get('logging', 'level', fallback='INFO')
        file = config.get('logging', 'file', fallback='convert.log')
        self.init_logger(level, file)
        db_file = config.get('logging', 'db', fallback='processed.shelve')
        self.db = ProcessedDatabase(db_file)

    def init_logger(self, level, file):
        level = logging.getLevelName(level)
        logging.basicConfig(level=level,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            handlers=[logging.FileHandler(file)]
                            )

    def backup_file(self, file, target_dir) -> subprocess.Popen:
        target_path = os.path.join(self.backup_path, target_dir)
        args = [self.rclone_exe, 'copy', '--transfers=1', '--timeout=4h0m0s',
                file,
                target_path]
        logger.debug(args)
        return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def backup(self, dir, file) -> Tuple[subprocess.Popen, str]:
        relative_file = file.replace(dir, '')
        if relative_file.startswith('/'):
            relative_file = relative_file[1::]
        target_dir = os.path.dirname(relative_file)

        size = os.path.getsize(file)
        if size >= self.max_size:
            logger.debug('{} will be split'.format(file))
            split_out_dir = os.path.join(self.working_dir, os.path.basename(file) + '_split')
            name = os.path.join(split_out_dir, os.path.basename(file) + '.')
            create_dirs(name)
            split_args = [self.split_exe, '-d', '-a', '2', '-b', self.split_size, file, name]
            logger.debug(split_args)
            ret = subprocess.run(split_args).returncode
            if ret != 0:
                logger.error('Error splitting, code={}, file={}'.format(ret, file))
                return None
            return self.backup_file(split_out_dir, target_dir), split_out_dir
        else:
            return self.backup_file(file, target_dir), None

    def check_input_name(self, file):
        name = os.path.basename(file)
        if TV_NAME_REGEX.match(name) or MOVIE_NAME_REGEX.match(name):
            return True
        else:
            return False

    def process(self, root_dir, input_file, output_file, temp_file, status):
        create_dirs(temp_file)
        create_dirs(output_file)
        # Start backup
        backup_popen, cleanup_dir = None, None
        if not status.backup:
            logger.debug('No backup for {}'.format(input_file))
            backup_popen, cleanup_dir = self.backup(root_dir, input_file)
        if not status.convert:
            # Start convert
            logger.debug('Not converted: {}'.format(input_file))
            if os.path.exists(output_file):
                logger.info(
                    'Output exists, skipping: input={}, output={}'.format(input_file, output_file))
            else:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                result = convert_with_config(input_file, temp_file, self.convert_config, print_output=False)
                if result == 0:
                    logger.debug('Conversion successful for {}'.format(input_file))
                    os.rename(temp_file, output_file)
                    status.convert = True
                else:
                    logger.error('Error converting: code={}, file={}'.format(result, input_file))
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
        if backup_popen:
            logger.debug('Waiting for backup...')
            ret_code = backup_popen.wait()

            if ret_code == 0:
                logger.debug('Backup succeeded for {}'.format(input_file))
                status.backup = True
                if cleanup_dir and os.path.exists(cleanup_dir):
                    shutil.rmtree(cleanup_dir, ignore_errors=True)
            else:
                logger.error('Error backing up: code={}, file={}'.format(ret_code, input_file))

    def run(self):
        logger.info('Starting new run')
        count = 0
        for in_dir, out_dir in [(self.movie_in_dir, self.movie_out_dir), (self.tv_in_dir, self.tv_out_dir)]:
            to_process = list(get_input_output(in_dir, out_dir, self.working_dir))
            for input_file, output_file, temp_file in to_process:
                try:
                    status = self.db.get(input_file, output_file)
                    if status.should_process():
                        m_time = datetime.fromtimestamp(os.path.getmtime(input_file))
                        if not self.check_input_name(input_file):
                            logger.warning('Invalid name, skipping: {}'.format(input_file))
                        elif m_time > (datetime.now() - timedelta(minutes=5)):
                            logger.debug('File too recently modified, skipping: {}'.format(input_file))
                        else:
                            logger.info('Starting {}'.format(input_file))
                            self.process(in_dir, input_file, output_file, temp_file, status)
                            self.db.save(status)
                            count += 1
                    else:
                        logger.debug('Not processing: {}'.format(input_file))
                except:
                    logger.exception('Exception while processing {}'.format(input_file))
        logger.info('Processed {} files'.format(count))


def main():
    import argparse, argcomplete

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='Sub commands', dest='command')
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('config', type=str)
    run_parser = subparsers.add_parser('run', help='Run the convert DVD process', parents=[parent_parser])
    list_parser = subparsers.add_parser('list', help='List files that have been processed successfully',
                                        parents=[parent_parser])

    argcomplete.autocomplete(parser)
    ns = vars(parser.parse_args())
    cmd = ns['command']
    config = ns['config']
    convert_dvds = ConvertDvds(config)

    if cmd == 'run':
        convert_dvds.run()
    elif cmd == 'list':
        for status in convert_dvds.db.get_all_existing_success():
            print(status.input_file)


if __name__ == '__main__':
    main()
