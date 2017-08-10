import argparse
import argcomplete

import media_management_scripts.support.files
from media_management_scripts.support.encoding import DEFAULT_CRF, DEFAULT_PRESET, AudioChannelName
from itertools import chain


def build_argparse():
    parser = argparse.ArgumentParser()
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('--print-args', action='store_const', const=True, default=False)
    parent_parser.add_argument('-n', '--dry-run', action='store_const', const=True, default=False)

    input_parser = argparse.ArgumentParser(add_help=False)
    input_parser.add_argument('input', help='Input directory')

    output_parser = argparse.ArgumentParser(add_help=False)
    output_parser.add_argument('output', help='Output target')
    output_parser.add_argument('-y', '--overwrite', help='Overwrite output target if it exists', action='store_const', default=False, const=True)

    subparsers = parser.add_subparsers(help='Sub commands', dest='command')

    find_episode_parser = subparsers.add_parser('find-episodes', help='Find Season/Episode/Part using file names',
                                                parents=[parent_parser, input_parser])

    find_episode_parser.add_argument('--strip-youtube-dl', default=True, type=bool)
    find_episode_parser.add_argument('--concat-files', action='store_const', const=True, default=False)
    find_episode_parser.add_argument('--output', '-o', default='./', dest='output')
    find_episode_parser.add_argument('--seasons', action='store_const', const=True, default=False,
                                     help='If renaming, moves files into season directories')
    find_episode_parser.add_argument('--ignore-parts', action='store_const', const=True, default=False)

    group = find_episode_parser.add_mutually_exclusive_group()
    group.add_argument('--rename', action='store_const', const=True, default=False,
                       help='Renames the files using the season & episode if found')
    group.add_argument('--copy', action='store_const', const=True, default=False,
                       help='Copies the file with new name to output directory')

    subparsers.add_parser('strip-youtube-dl', help='Remove the playlist index prefix from files',
                          parents=[parent_parser, input_parser])

    metadata_parser = subparsers.add_parser('metadata', help='Show metadata for a file',
                                            parents=[parent_parser, input_parser])
    metadata_group = metadata_parser.add_mutually_exclusive_group()
    metadata_group.add_argument('--popup', action='store_const', const=True, default=False)
    metadata_group.add_argument('--json', '-j', action='store_const', const=True, default=False)
    metadata_parser.add_argument('--interlace', help='Try to detect interlacing',
                                 choices=['none', 'summary', 'report'], default='none')
    concat_mp4_parser = subparsers.add_parser('concat-mp4', help='Concat multiple mp4 files together',
                                              parents=[])  # No input dir
    concat_mp4_parser.add_argument('output', help='The output file')
    concat_mp4_parser.add_argument('input', nargs='*',
                                   help='The input files to concat. These must be mp4 with h264 codec.')

    convert_parent_parser = argparse.ArgumentParser(add_help=False, parents=[output_parser])
    convert_parent_parser.add_argument('--crf', default=DEFAULT_CRF, type=int,
                                       help='The CRF value for H.264 transcoding. Default={}'.format(DEFAULT_CRF))
    convert_parent_parser.add_argument('--preset', default=DEFAULT_PRESET,
                                       choices=['ultrafast', 'superfast', DEFAULT_PRESET, 'faster', 'fast', 'medium',
                                                'slow',
                                                'slower', 'veryslow', 'placebo'],
                                       help='The preset for H.264 transcoding. Default={}'.format(DEFAULT_PRESET))
    convert_parent_parser.add_argument('--bitrate', default=None,
                                       help='Use variable bitrate up to this value. Default=None (ignored). Specify "auto" for automatic bitrate.')
    convert_parent_parser.add_argument('--deinterlace', action='store_const', const=True, default=False,
                                       help="Attempt to detect interlacing and remove it")
    convert_parent_parser.add_argument('--deinterlace-threshold', type=float, default=.5)
    convert_parent_parser.add_argument('--add-ripped-metadata', action='store_const', const=True, default=False,
                                       help='Adds a metadata item to the output indicating this is a ripped video',
                                       dest='include_meta')

    convert_dvd_parser = subparsers.add_parser('convert-dvds', help='Convert ripped DVDs',
                                               parents=[parent_parser, input_parser, convert_parent_parser])
    convert_dvd_parser.add_argument('--compare', action='store_const', const=True, default=False)

    convert_parser = subparsers.add_parser('convert', help='Convert to H.264 & AAC',
                                           parents=[parent_parser, input_parser, convert_parent_parser])

    combine_video_subtitles_parser = subparsers.add_parser('combine', help='Combine a video files with subtitle file',
                                                           parents=[parent_parser, input_parser, convert_parent_parser])
    combine_video_subtitles_parser.add_argument('input-subtitles', help='The subtitle file')
    combine_video_subtitles_parser.add_argument('--convert',
                                                help='Whether to convert video streams to H.264 and audio to AAC',
                                                action='store_const', const=True, default=False)

    combine_all_parser = subparsers.add_parser('combine-all',
                                               help='Combine a directory tree of video files with subtitle file',
                                               parents=[parent_parser, input_parser, convert_parent_parser])
    combine_all_parser.add_argument('--convert',
                                    help='Whether to convert video streams to H.264 and audio to AAC',
                                    action='store_const', const=True, default=False)

    tv_rename_parser = subparsers.add_parser('tv-rename', help='Renames files in a directory to sXXeYY',
                                             parents=[parent_parser])
    tv_rename_parser.add_argument('-s', '--season', default=1, help='The season to use', type=int)
    tv_rename_parser.add_argument('-e', '--episode', default=1, help='The episode to start with', type=int)
    tv_rename_parser.add_argument('--show', default=None, help='The name of the show', type=str)
    tv_rename_parser.add_argument('--output', default=None, help='The output directory to move & rename to', type=str)
    tv_rename_parser.add_argument('input', nargs='*',
                                  help='The directories to search for files. These will be processed in order.')

    movie_rename_parser = subparsers.add_parser('movie-rename', help='Renames a file based on TheMovieDB',
                                                parents=[parent_parser])
    movie_rename_parser.add_argument('--confirm',
                                     help='Ask for confirmation before renaming, exiting with non-zero if no',
                                     action='store_const', const=True, default=False)
    movie_rename_parser.add_argument('--username')
    movie_rename_parser.add_argument('--host')
    movie_rename_parser.add_argument('--pkey')
    movie_rename_parser.add_argument('--output-path')
    movie_rename_parser.add_argument('--move-source-path', default=None)
    movie_rename_parser.add_argument('input', nargs='+', help='Input Files')

    search_parser = subparsers.add_parser('search', help='Searches files matching parameters',
                                          parents=[parent_parser, input_parser])
    search_parser.add_argument('--db', default=None, dest='db_file')
    # search_parser.add_argument('-v', '--video-codec', help='Match video codec', type=str)
    # search_parser.add_argument('-a', '--audio-codec', help='Match audio codec', type=str)
    # search_parser.add_argument('--ac', '--audio-channels', help='Match audio channels', type=str, dest='audio_channels',
    #                            choices=list(chain(*[ac.names for ac in list(AudioChannelName)])))
    # search_parser.add_argument('-s', '--subtitle', help='Match subtitle language', type=str)
    # search_parser.add_argument('-c', '--container', help='Match container', type=str)
    # search_parser.add_argument('-r', '--resolution', help='Match resolution', type=str)
    # search_parser.add_argument('--not', help='Invert filter', action='store_const', const=True, default=False)
    search_parser.add_argument('query')
    search_parser.add_argument('-0', help='Output with null byte', action='store_const', const=True, default=False)

    split_parser = subparsers.add_parser('split', help='Split a file', parents=[parent_parser, input_parser])
    split_parser.add_argument('-c', '--by-chapters', help='Split file by chapters, specifying number of episodes',
                              type=int)
    split_parser.add_argument('--output', '-o', default='./', dest='output')

    index_rclone = subparsers.add_parser('index-rclone', help='Index rclone output into a sqlite file',
                                         parents=[parent_parser])
    index_rclone.add_argument('output')

    rename_parser = subparsers.add_parser('rename', parents=[parent_parser],
                                          help="Renames a set of files to the specified template",
                                          formatter_class=argparse.RawTextHelpFormatter,
                                          description="""
Rename files based on a template.
                                          
Templates can include variables or expressions by surrounding with ${...}. Functions can be called like ${upper(i)} or ${i | upper}.
 
The following variables are available:
    * i/index - The index of the current file being renamed
    * ext - The file extension of the current file
    * filename - The filename of the current file (basename)
    * re/regex - A list of regex match groups (use re[0], re[1], etc)

The following functions are available:
    * upper - Upper cases the input
    * lower - Lower cases the input
    * ifempty(a, b) - If a is not null, then a, otherwise b
    * lpad(a, b:int) - Left pads a to length b (defaults to 2) with spaces
    * zpad(a, b:int) - Left pads a to length b (defaults to 2) with zeros
    
Regular Expressions:
If a regex is included, the match groups (0=whole match, >0=match group) are avaiable in a list 're' or 'regex'.
Each match group is converted to an int if possible, so a zero padded int will lose the zeros.

Examples:
    Input: S02E04.mp4
    Regex: S(\d+)E(\d+)
    
    Template: 'Season ${re[1]} Episode ${re[2]}.{ext}'
    Result: 'Season 2 Episode 4.mp4'
    
    Template: Template: 'Season ${re[1] | zpad} Episode ${zpad(re[2], 3)}.{ext}'
    Results: 'Season 02 Episode 004.mp4'
    
            
    Input: whatever.mp4
    Regex: S(\d+)E(\d)
    Template: 'Season ${ifempty(re[1], 'unknown')} Episode ${re[2]}.{ext}'
    Result: 'Season unknown Episode .mp4'
    """)

    rename_parser.add_argument('-x', '--regex', type=str, default=None)
    rename_parser.add_argument('--ignore-missing-regex', action='store_const', default=False, const=True,
                               dest='ignore_missing_regex')
    rename_parser.add_argument('-i', '--index-start', type=int, default=1)
    rename_parser.add_argument('-o', '--output', default=None)
    rename_parser.add_argument('-r', '--recursive', action='store_const', default=False, const=True)
    rename_parser.add_argument('--filter-by-ext', type=str, default=None)
    rename_parser.add_argument('template')
    rename_parser.add_argument('input', nargs='+', help='Input files')

    itunes_parser = subparsers.add_parser('itunes', parents=[parent_parser])
    itunes_parser.add_argument('-o', '--output', type=str, default='./')
    itunes_parser.add_argument('--meta-shelve', type=str, default=None, dest='meta_shelve')
    itunes_parser.add_argument('input', nargs='+', help='Input files')
    itunes_parser.add_argument('--dvd', action='store_const', default=False, const=True)
    itunes_parser.add_argument('--fuzzy', action='store_const', default=False, const=True)

    stream_select_parser = subparsers.add_parser('stream-select',
                                                 parents=[parent_parser, input_parser, convert_parent_parser])
    stream_select_parser.add_argument('-c', '--convert', action='store_const', default=False, const=True,
                               help='Whether to convert the file or just remux it')

    argcomplete.autocomplete(parser)
    return parser


def _find_episodes_command(ns):
    import os
    from media_management_scripts.support.episode_finder import find_episodes
    from media_management_scripts.utils import season_episode_name
    from shutil import copyfile, move
    from media_management_scripts.support.concat_mp4 import concat_mp4

    concat = {}
    input = ns['input']
    do_new_name = ns.get('rename', False) or ns.get('copy', False)
    out_dir = ns['output']
    ignore_parts = ns['ignore_parts']
    season_folders = ns.get('seasons', False)
    # for ep in sorted(find_episodes(input, ns['strip_youtube_dl']), key=lambda x: (x.season, x.episode, x.part)):
    for ep in find_episodes(input, ns['strip_youtube_dl']):
        if ep.part and ep.season and ep.episode and not ignore_parts:
            key = (ep.season, ep.episode)
            eps = concat.get(key, [])
            eps.append(ep)
            concat[key] = eps
        elif do_new_name and ep.season and ep.episode:
            path = ep.path
            filename = os.path.basename(path)
            name, ext = os.path.splitext(filename)

            new_name = season_episode_name(ep.season, int(ep.episode), ext)
            if season_folders:
                season_f = os.path.join(out_dir, 'Season {}'.format(ep.season))
            else:
                season_f = out_dir
            if not os.path.exists(season_f):
                os.makedirs(season_f)
            if ns.get('rename', False):
                out_file = os.path.join(season_f, new_name)
                print('{} -> {}'.format(filename, out_file))
                move(path, out_file)
            else:
                out_file = os.path.join(season_f, new_name)
                print('{} -> {}'.format(filename, out_file))
                copyfile(path, out_file)
        else:
            print(ep)
    for key in concat:
        list = sorted(concat[key])
        print('s{}e{}'.format(key[0], key[1]))
        for item in list:
            print('   {} pt{}'.format(item.name, item.part))
        if ns['concat_files']:
            to_concat = [item.path for item in list]
            if len(to_concat) > 1:
                if season_folders:
                    season_f = os.path.join(out_dir, 'Season {}'.format(key[0]))
                else:
                    season_f = out_dir
                if not os.path.exists(season_f):
                    os.makedirs(season_f)
                output_file = os.path.join(season_f, season_episode_name(key[0], key[1], '.mp4'))
                print('Concating files: {} -> {}'.format(to_concat, output_file))
                concat_mp4(output_file, to_concat)


def execute(ns):
    import os
    import re
    import sys
    import shutil

    from media_management_scripts.convert import ConvertConfig, convert_config_from_ns
    from media_management_scripts.support.files import list_files
    from media_management_scripts import convert, renamer
    from media_management_scripts.print_metadata import print_metadata, print_metadata_json
    from media_management_scripts.support.concat_mp4 import concat_mp4
    from media_management_scripts.support.combine_all import combine_all, get_lang
    from media_management_scripts.search import search, SearchParameters
    from media_management_scripts.support.split import split_by_chapter
    from media_management_scripts.moviedb import MovieDbApi
    from media_management_scripts.index_rclone_ls import from_stdin

    input_to_cmd = ns.get('input', None)
    cmd = ns['command']
    if cmd == 'find-episodes':
        _find_episodes_command(ns)
    elif cmd == 'strip-youtube-dl':
        pattern = re.compile('\d+ - .+\.mp4')
        for root, subdirs, files in os.walk(input_to_cmd):
            for file in files:
                source = os.path.join(root, file)
                if pattern.match(file):
                    index = file.index(' - ')
                    out_path = os.path.join(root, file[index + 3::])
                    print('{} -> {}'.format(source, out_path))
                    if not ns['dry_run']:
                        os.rename(source, out_path)
    elif cmd == 'metadata':
        if ns['json']:
            print_metadata_json(input_to_cmd, ns['interlace'])
        else:
            print_metadata(input_to_cmd, ns['popup'], ns['interlace'])
    elif cmd == 'concat-mp4':
        output_file = ns['output']
        concat_mp4(output_file, input_to_cmd)
    elif cmd == 'convert-dvds':
        output = ns['output']
        if ns['compare']:
            convert.do_compare(input_to_cmd, output)
        elif ns['dry_run']:
            for i, o in media_management_scripts.support.files.get_input_output(input_to_cmd, output):
                print('{} -> {}'.format(i, o))
        else:
            config = convert_config_from_ns(ns)
            convert.main(input_to_cmd, output, config)
    elif cmd == 'convert':
        output = ns['output']
        config = convert_config_from_ns(ns)
        if os.path.exists(output):
            print('Cowardly refusing to overwrite existing file: {}'.format(output))
        else:
            convert.convert_with_config(input_to_cmd, output, config, print_output=True)
    elif cmd == 'combine':
        srt_input = ns['input-subtitles']
        output = ns['output']
        if not output.endswith('.mkv'):
            print('Output must be a MKV file')
            sys.exit(1)
        crf = ns.get('crf', DEFAULT_CRF)
        preset = ns.get('preset', DEFAULT_PRESET)
        convert = ns.get('convert', False)
        lang = get_lang(srt_input)
        convert.combine(input_to_cmd, srt_input, output, convert=convert, crf=crf, preset=preset, lang=lang)
    elif cmd == 'combine-all':
        crf = ns.get('crf', DEFAULT_CRF)
        preset = ns.get('preset', DEFAULT_PRESET)
        convert = ns.get('convert', False)
        output = ns['output']
        combine_all(input_to_cmd, output, convert, crf, preset)
    elif cmd == 'tv-rename':
        season = ns.get('season', 1)
        episode = ns.get('episode', 1)
        show = ns.get('show', None)
        dry_run = ns.get('dry_run', False)
        output = ns.get('output', None)
        renamer.run(input_to_cmd, season, episode, show, dry_run, output)
    elif cmd == 'movie-rename':
        from media_management_scripts.support.movie_rename import movie_rename
        movie_rename(input_to_cmd, ns)
    elif cmd == 'search':
        null_byte = ns['0']
        query = ns['query']
        db_file = ns['db_file']
        l = []
        for file, metadata in search(input_to_cmd, query, db_file):
            if not null_byte:
                print(file)
            else:
                l.append(file)
        if null_byte:
            print('\0'.join(l))
    elif cmd == 'split':
        output = ns['output']
        if 'by_chapters' in ns:
            episodes = ns['by_chapters']
            split_by_chapter(input_to_cmd, output, episodes)
        else:
            raise Exception('Unsupported')
    elif cmd == 'index-rclone':
        output = ns['output']
        from_stdin(output)
    elif cmd == 'rename':
        from texttable import Texttable
        template = ns['template']
        output = ns['output']
        regex = ns['regex']
        index_start = ns['index_start']
        recursive = ns['recursive']
        ignore_missing_regex = ns['ignore_missing_regex']
        filter_by_ext = ns['filter_by_ext']
        if recursive:
            if filter_by_ext:
                filter = lambda f: f.endswith(filter_by_ext)
            else:
                filter = lambda f: True
            files = []
            for f in input_to_cmd:
                if os.path.isdir(f):
                    files.extend(list_files(f, filter=filter))
                else:
                    files.append(f)
        else:
            files = input_to_cmd

        results = renamer.rename_process(template, files, index_start, output, regex,
                                         ignore_missing_regex=ignore_missing_regex)
        if ns['dry_run']:
            t = Texttable(max_width=0)
            t.set_deco(Texttable.VLINES | Texttable.HEADER)
            t.add_rows([('Source', 'Destination')] + results)
            print(t.draw())
        else:
            for src, dest in results:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.move(src, dest)
    elif cmd == 'curses':
        from media_management_scripts.interface import do_interface
        do_interface()
    elif cmd == 'itunes':
        from media_management_scripts.itunes import process_itunes_tv
        from media_management_scripts.tvdb_api import from_config
        tvdb = from_config(os.path.expanduser('~/.config/tvdb/tvdb.ini'))
        output = ns['output']
        dvd = ns['dvd']
        fuzzy = ns['fuzzy']
        meta_shelve = ns['meta_shelve']
        dry_run = ns['dry_run']
        if meta_shelve:
            import shelve
            with shelve.open(meta_shelve) as meta_store:
                process_itunes_tv(input_to_cmd, output, tvdb, meta_shelve=meta_store, use_dvd=dvd, fuzzy=fuzzy,
                                  dry_run=dry_run)
        else:
            process_itunes_tv(input_to_cmd, output, tvdb, meta_shelve=None, use_dvd=dvd, fuzzy=fuzzy, dry_run=dry_run)
    elif cmd == 'stream-select':
        from media_management_scripts.stream_selector import select_streams
        convert_config = convert_config_from_ns(ns) if ns['convert'] else None
        output_file=ns['output']
        overwrite = ns['overwrite']
        select_streams(input_to_cmd, output_file, overwrite=overwrite, convert_config=convert_config)
    else:
        raise Exception('Unknown command')


def main():
    parser = build_argparse()
    ns = vars(parser.parse_args())
    if ns.get('print_args', False):
        print(ns)
    elif ns.get('command', None) is None:
        parser.print_usage()
    else:
        execute(ns)


if __name__ == '__main__':
    main()
