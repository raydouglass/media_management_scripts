import configparser
import logging
import logging.config
import os
import re
import shlex
import shutil
import sqlite3
import subprocess
from datetime import datetime, timedelta
from typing import Tuple, NamedTuple

from media_management_scripts.convert import convert_with_config
from media_management_scripts.support.files import create_dirs, get_input_output
from media_management_scripts.utils import convert_config_from_config_section

logger = logging.getLogger(__name__)

TV_NAME_REGEX = re.compile(r".+ - S\d{2,}E\d{2,}(-E\d{2,})?( - .+)?\.mkv")
MOVIE_NAME_REGEX = re.compile(r".+ \(\d{4}\)( - .+)?\.mkv")


class ConvertDvdResults(NamedTuple):
    movie_processed_count: int
    movie_total_count: int
    movie_error_count: int
    tv_processed_count: int
    tv_total_count: int
    tv_error_count: int


class ProcessStatus:
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
        return "<ProcessStatus: input={}, output={}, backup={}, convert={}>".format(
            self.input_file, self.output_file, self.backup, self.convert
        )


class ProcessedDatabase:
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS processed(input PRIMARY KEY, output VARCHAR, backup BOOLEAN, convert BOOLEAN);"
        )
        self.conn.commit()

    def get(self, input_file, output_file):
        logger.debug("Getting: {}".format(input_file))
        row = self.conn.execute(
            "SELECT backup, convert FROM processed WHERE input = ?", (input_file,)
        ).fetchone()
        if row:
            status = ProcessStatus(input_file, output_file, row[0] == 1, row[1] == 1)
            logger.debug("Found: {}".format(status))
        else:
            logger.debug("Not found, saving new")
            status = ProcessStatus(input_file, output_file)
            self.save(status)
        return status

    def save(self, status):
        logger.debug("Saving: {}".format(status))
        self.conn.execute(
            "REPLACE INTO processed (input, output, backup, convert) VALUES (?, ?, ?, ?);",
            (status.input_file, status.output_file, status.backup, status.convert),
        )
        self.conn.commit()


class ConvertDvds:
    def __init__(self, config_file):
        config = configparser.ConfigParser()
        config.read(config_file)

        # Directories
        self.movie_in_dir = config.get("directories", "movie.dir.in")
        self.tv_in_dir = config.get("directories", "tv.dir.in")
        self.working_dir = config.get("directories", "working.dir")
        self.movie_out_dir = config.get("directories", "movie.dir.out")
        self.tv_out_dir = config.get("directories", "tv.dir.out")

        # Backup
        self.backup_enabled = config.getboolean("backup", "enabled", fallback=True)
        self.rclone_exe = config.get("backup", "rclone")
        self.rclone_args = shlex.split(config.get("backup", "rclone.args", fallback=""))
        self.split_exe = config.get("backup", "split")
        self.backup_path = config.get("backup", "backup.path")
        self.max_size = int(config.get("backup", "max.size")) * (1024**3)
        self.split_size = config.get("backup", "split.size")

        self.movie_convert_config = convert_config_from_config_section(
            config, "movie.transcode"
        )
        self.tv_convert_config = convert_config_from_config_section(
            config, "tv.transcode"
        )

        if config.has_section("transcode"):
            raise Exception(
                "Config file is out dated. Please update to use movie.transcode and tv.transcode"
            )

        # Logging
        file = config.get("logging", "config", fallback=None)
        if file:
            import yaml

            with open(file) as f:
                log_config = yaml.safe_load(f)
                logging.config.dictConfig(log_config)
        db_file = config.get("logging", "db", fallback="processed.shelve")
        self.db = ProcessedDatabase(db_file)

    def backup_file(self, file, target_dir) -> subprocess.Popen:
        target_path = os.path.join(self.backup_path, target_dir)
        args = [self.rclone_exe, "copy", "--transfers=1"]
        if self.rclone_args:
            args.extend(self.rclone_args)
        args.extend([file, target_path])
        logger.debug(args)
        return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def backup(self, dir, file) -> Tuple[subprocess.Popen, str]:
        relative_file = file.replace(dir, "")
        if relative_file.startswith("/"):
            relative_file = relative_file[1::]
        target_dir = os.path.dirname(relative_file)

        size = os.path.getsize(file)
        if size >= self.max_size:
            logger.debug("{} will be split".format(file))
            split_out_dir = os.path.join(
                self.working_dir, os.path.basename(file) + "_split"
            )
            name = os.path.join(split_out_dir, os.path.basename(file) + ".")
            create_dirs(name)
            split_args = [
                self.split_exe,
                "-d",
                "-a",
                "2",
                "-b",
                self.split_size,
                file,
                name,
            ]
            logger.debug(split_args)
            ret = subprocess.run(split_args).returncode
            if ret != 0:
                logger.error("Error splitting, code={}, file={}".format(ret, file))
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

    def process(
        self, root_dir, input_file, output_file, temp_file, status, convert_config
    ):
        if not status.convert and os.path.exists(output_file):
            logger.info(
                "Output exists, will not convert: input={}, output={}".format(
                    input_file, output_file
                )
            )
        create_dirs(temp_file)
        create_dirs(output_file)
        # Start backup
        backup_popen, cleanup_dir = None, None
        error = False
        if not status.backup:
            if self.backup_enabled:
                logger.debug("No backup for {}".format(input_file))
                backup_popen, cleanup_dir = self.backup(root_dir, input_file)
            else:
                logger.debug(
                    "No backup for {}, but backups are disabled".format(input_file)
                )
        if not status.convert and not os.path.exists(output_file):
            # Start convert
            logger.debug("Not converted: {}".format(input_file))
            if os.path.exists(temp_file):
                os.remove(temp_file)
            result = convert_with_config(
                input_file, temp_file, convert_config, print_output=False
            )
            if result == 0:
                logger.debug("Conversion successful for {}".format(input_file))
                shutil.copyfile(temp_file, output_file)
                status.convert = True
            else:
                logger.error(
                    "Error converting: code={}, file={}".format(result, input_file)
                )
                error = True
            if os.path.exists(temp_file):
                os.remove(temp_file)
        if backup_popen:
            logger.debug("Waiting for backup...")
            ret_code = backup_popen.wait()

            if ret_code == 0:
                logger.debug("Backup succeeded for {}".format(input_file))
                status.backup = True
                if cleanup_dir and os.path.exists(cleanup_dir):
                    shutil.rmtree(cleanup_dir, ignore_errors=True)
            else:
                logger.error(
                    "Error backing up: code={}, file={}".format(ret_code, input_file)
                )
                error = True
        return not error

    def _run(self, in_dir, out_dir, convert_config):
        total_files = 0
        count = 0
        error_count = 0
        to_process = list(get_input_output(in_dir, out_dir, self.working_dir))
        for input_file, output_file, temp_file in to_process:
            total_files += 1
            try:
                status = self.db.get(input_file, output_file)
                if status.should_process():
                    m_time = datetime.fromtimestamp(os.path.getmtime(input_file))
                    if not self.check_input_name(input_file):
                        logger.warning("Invalid name, skipping: {}".format(input_file))
                    elif m_time > (datetime.now() - timedelta(minutes=5)):
                        logger.debug(
                            "File too recently modified, skipping: {}".format(
                                input_file
                            )
                        )
                    else:
                        logger.info("Starting {}".format(input_file))
                        if self.process(
                            in_dir,
                            input_file,
                            output_file,
                            temp_file,
                            status,
                            convert_config,
                        ):
                            count += 1
                        self.db.save(status)
                else:
                    logger.debug("Not processing: {}".format(input_file))
            except:
                logger.exception("Exception while processing {}".format(input_file))
                error_count += 1
        return count, total_files, error_count

    def run(self):
        logger.info("Starting new run")
        movie_counts = self._run(
            self.movie_in_dir, self.movie_out_dir, self.movie_convert_config
        )
        tv_counts = self._run(self.tv_in_dir, self.tv_out_dir, self.tv_convert_config)
        logger.info("Processed {} of {} movie files ({} errors)".format(*movie_counts))
        logger.info("Processed {} of {} tv files ({} errors)".format(*tv_counts))
        return ConvertDvdResults(*movie_counts, *tv_counts)

    def get_existing_success(self, in_dir, out_dir):
        for input_file, output_file in get_input_output(in_dir, out_dir):
            if os.path.exists(output_file):
                status = self.db.get(input_file, output_file)
                if status.backup and status.convert:
                    yield input_file

    def get_all_existing_success(self):
        from itertools import chain

        return chain(
            self.get_existing_success(self.movie_in_dir, self.movie_out_dir),
            self.get_existing_success(self.tv_in_dir, self.tv_out_dir),
        )


def main():
    import argparse, argcomplete

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Sub commands", dest="command")
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("config", type=str)
    run_parser = subparsers.add_parser(
        "run", help="Run the convert DVD process", parents=[parent_parser]
    )
    list_parser = subparsers.add_parser(
        "list",
        help="List files that have been processed successfully",
        parents=[parent_parser],
    )
    list_parser.add_argument("-0", action="store_const", const=True, default=False)

    argcomplete.autocomplete(parser)
    ns = vars(parser.parse_args())
    cmd = ns["command"]
    config = ns["config"]
    convert_dvds = ConvertDvds(config)

    if cmd == "run":
        convert_dvds.run()
    elif cmd == "list":
        results = convert_dvds.get_all_existing_success()
        for r in results:
            if ns["0"]:
                print(r, end="\0")
            else:
                print(r)


if __name__ == "__main__":
    main()
