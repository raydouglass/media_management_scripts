import argparse

from media_management_scripts.silver_tube.delete_process import run_delete


def create_arg_parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='Sub commands', dest='command')

    process_parser = subparsers.add_parser('process', help='Process recorded TV files')
    process_parser.add_argument('config', type=str, help='Configuration file')
    process_parser.add_argument('--tvdb-config', type=str, help='TVDB credential file', default=None)

    db_parser = subparsers.add_parser('db', help='Handle unmatched files in database')
    db_parser.add_argument('--skip-no-options', '-s', help='Skip files which have zero options', dest='skip_no_options',
                           default=False, action='store_const', const=True)
    db_parser.add_argument('db-file', type=str, help='Database file')

    delete_parser = subparsers.add_parser('delete', help='Delete recorded TV files')
    delete_parser.add_argument('config', type=str, help='Configuration file')

    return parser


def handle(ns):
    cmd = ns['command']
    if cmd == 'process':
        from media_management_scripts.silver_tube.processing import Configuration
        from media_management_scripts.tvdb_api import from_config, DEFAULT_CONFIG_LOCATION
        config_file = ns['config']
        tvdb = from_config(ns.get('tvdb_config', DEFAULT_CONFIG_LOCATION))
        config = Configuration(config_file, tvdb)
        config.run()
    elif cmd == 'db':
        from media_management_scripts.silver_tube.wtv_db import WtvDb
        db_file = ns['db_file']
        wtvdb = WtvDb(db_file)
        skip_no_options = ns['skip_no_options']
        wtvdb.begin()
        wtvdb.resolve_all(skip_no_options)
        wtvdb.end()
    elif cmd == 'delete':
        config_file = ns['config']
        run_delete(config_file)


def main():
    parser = create_arg_parse()
    ns = vars(parser.parse_args())
    handle(ns)
