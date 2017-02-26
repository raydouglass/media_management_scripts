import argparse
import os
import re
import sys
from shutil import copyfile, move

from media_management_scripts import convert_dvd, renamer
from media_management_scripts.support.episode_finder import find_episodes

from media_management_scripts.print_metadata import print_metadata
from media_management_scripts.support.concat_mp4 import concat_mp4
from media_management_scripts.support.combine_all import combine_all, get_lang
from media_management_scripts.support.encoding import DEFAULT_CRF, DEFAULT_PRESET
from media_management_scripts.utils import season_episode_name
from media_management_scripts.search import search, SearchParameters
from media_management_scripts.support.split import split_by_chapter


def build_argparse():
    parser = argparse.ArgumentParser()
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('--print-args', action='store_const', const=True, default=False)
    parent_parser.add_argument('--dry-run', action='store_const', const=True, default=False)

    input_parser = argparse.ArgumentParser(add_help=False)
    input_parser.add_argument('input', help='Input directory')

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
    metadata_parser.add_argument('--popup', action='store_const', const=True, default=False)

    concat_mp4_parser = subparsers.add_parser('concat-mp4', help='Remove the playlist index prefix from files',
                                              parents=[])  # No input dir
    concat_mp4_parser.add_argument('output', help='The output file')
    concat_mp4_parser.add_argument('input', nargs='*',
                                   help='The input files to concat. These must be mp4 with h264 codec.')

    convert_parent_parser = argparse.ArgumentParser(add_help=False)
    convert_parent_parser.add_argument('--crf', default=DEFAULT_CRF, type=int,
                                       help='The CRF value for H.264 transcoding. Default={}'.format(DEFAULT_CRF))
    convert_parent_parser.add_argument('--preset', default=DEFAULT_PRESET,
                                       choices=['ultrafast', 'superfast', DEFAULT_PRESET, 'faster', 'fast', 'medium',
                                                'slow',
                                                'slower', 'veryslow', 'placebo'],
                                       help='The preset for H.264 transcoding. Default={}'.format(DEFAULT_PRESET))
    convert_parent_parser.add_argument('--bitrate', default=None,
                                       help='Use variable bitrate up to this value. Default=None (ignored). Specify "auto" for automatic bitrate.')
    convert_parent_parser.add_argument('output')

    convert_dvd_parser = subparsers.add_parser('convert-dvds', help='Convert ripped DVDs',
                                               parents=[parent_parser, input_parser, convert_parent_parser])
    convert_dvd_parser.add_argument('--compare', action='store_const', const=True, default=False)

    convert_parser = subparsers.add_parser('convert', help='Convert to H.264 & AAC',
                                           parents=[parent_parser, input_parser, convert_parent_parser])
    convert_parser.add_argument('--add-ripped-metadata', action='store_const', const=True, default=False,
                                help='Adds a metadata item to the output indicating this is a ripped video')

    combine_video_subtitles_parser = subparsers.add_parser('combine', help='Combine a video files with subtitle file',
                                                           parents=[parent_parser, input_parser, convert_parent_parser])
    combine_video_subtitles_parser.add_argument('input-subtitles', help='The subtitle file')
    combine_video_subtitles_parser.add_argument('--convert',
                                                help='Whether to convert video streams to H.264 and audio to AAC',
                                                action='store_const', const=True, default=False)

    combine_all_parser = subparsers.add_parser('combine-all', help='Combine a video files with subtitle file',
                                               parents=[parent_parser, input_parser, convert_parent_parser])
    combine_all_parser.add_argument('--convert',
                                    help='Whether to convert video streams to H.264 and audio to AAC',
                                    action='store_const', const=True, default=False)
    rename_parser = subparsers.add_parser('rename', help='Renames files in a directory to sXXeYY',
                                          parents=[parent_parser])
    rename_parser.add_argument('-s', '--season', default=1, help='The season to use', type=int)
    rename_parser.add_argument('-e', '--episode', default=1, help='The episode to start with', type=int)
    rename_parser.add_argument('--show', default=None, help='The name of the show', type=str)
    rename_parser.add_argument('--output', default=None, help='The output directory to move & rename to', type=str)
    rename_parser.add_argument('input', nargs='*',
                               help='The directories to search for files. These will be processed in order.')

    search_parser = subparsers.add_parser('search', help='Searches files matching parameters',
                                          parents=[parent_parser, input_parser])
    search_parser.add_argument('-v', '--video-codec', help='Match video codec', type=str)
    search_parser.add_argument('-a', '--audio-codec', help='Match audio codec', type=str)
    search_parser.add_argument('-s', '--subtitle', help='Match subtitle language', type=str)
    search_parser.add_argument('-c', '--container', help='Match container', type=str)
    search_parser.add_argument('-r', '--resolution', help='Match resolution', type=str)
    search_parser.add_argument('--not', help='Invert filter', action='store_const', const=True, default=False)
    search_parser.add_argument('-0', help='Output with null byte', action='store_const', const=True, default=False)

    split_parser = subparsers.add_parser('split', help='Split a file', parents=[parent_parser, input_parser])
    split_parser.add_argument('-c', '--by-chapters', help='Split file by chapters, specifying number of episodes',
                              type=int)
    split_parser.add_argument('--output', '-o', default='./', dest='output')

    return parser


def _find_episodes_command(ns):
    concat = {}
    input = ns['input']
    do_new_name = ns.get('rename', False) or ns.get('copy', False)
    out_dir = ns['output']
    ignore_parts = ns['ignore_parts']
    season_folders = ns.get('seasons', False)
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
            if ns.get('rename', False):
                out_dir = os.path.dirname(path)
                out_file = os.path.join(out_dir, new_name)
                print('{} -> {}'.format(filename, out_file))
                move(path, out_file)
            else:
                if season_folders:
                    season_f = os.path.join(out_dir, 'Season {}'.format(ep.season))
                else:
                    season_f = out_dir
                if not os.path.exists(season_f):
                    os.makedirs(season_f)
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
    input = ns['input']
    cmd = ns['command']
    if cmd == 'find-episodes':
        _find_episodes_command(ns)
    elif cmd == 'strip-youtube-dl':
        pattern = re.compile('\d+ - .+\.mp4')
        for root, subdirs, files in os.walk(input):
            for file in files:
                source = os.path.join(root, file)
                if pattern.match(file):
                    index = file.index(' - ')
                    out_path = os.path.join(root, file[index + 3::])
                    print('{} -> {}'.format(source, out_path))
                    if not ns['dry_run']:
                        os.rename(source, out_path)
    elif cmd == 'metadata':
        print_metadata(input, ns['popup'])
    elif cmd == 'concat-mp4':
        output_file = ns['output']
        concat_mp4(output_file, input)
    elif cmd == 'convert-dvds':
        output = ns['output']
        if ns['compare']:
            convert_dvd.do_compare(input, output)
        elif ns['dry_run']:
            for i, o in convert_dvd.get_input_output(input, output):
                print('{} -> {}'.format(i, o))
        else:
            crf = ns.get('crf', DEFAULT_CRF)
            preset = ns.get('preset', DEFAULT_PRESET)
            bitrate = ns.get('bitrate', None)
            convert_dvd.main(input, output, crf, preset, bitrate=bitrate)
    elif cmd == 'convert':
        output = ns['output']
        crf = ns.get('crf', DEFAULT_CRF)
        preset = ns.get('preset', DEFAULT_PRESET)
        bitrate = ns.get('bitrate', None)
        if os.path.exists(output):
            print('Cowardly refusing to overwrite existing file: {}'.format(output))
        else:
            convert_dvd.convert(input, output, crf, preset, bitrate=bitrate, include_meta=ns['add_ripped_metadata'])
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
        convert_dvd.combine(input, srt_input, output, convert=convert, crf=crf, preset=preset, lang=lang)
    elif cmd == 'combine-all':
        crf = ns.get('crf', DEFAULT_CRF)
        preset = ns.get('preset', DEFAULT_PRESET)
        convert = ns.get('convert', False)
        output = ns['output']
        combine_all(input, output, convert, crf, preset)
    elif cmd == 'rename':
        season = ns.get('season', 1)
        episode = ns.get('episode', 1)
        show = ns.get('show', None)
        dry_run = ns.get('dry_run', False)
        output = ns.get('output', None)
        renamer.run(input, season, episode, show, dry_run, output)
    elif cmd == 'search':
        null_byte = ns['0']
        search_params = SearchParameters(ns)
        l = []
        for file, metadata in search(input, search_params):
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
            split_by_chapter(input, output, episodes)
        else:
            raise Exception('Unsupported')
    else:
        raise Exception('Unknown command')


def main():
    parser = build_argparse()
    ns = vars(parser.parse_args())
    if ns['print_args']:
        print(ns)
    else:
        execute(ns)


if __name__ == '__main__':
    main()
