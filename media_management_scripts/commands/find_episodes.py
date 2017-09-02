from . import SubCommand
from .common import *


class FindEpisodesCommand(SubCommand):
    @property
    def name(self):
        return 'find-episodes'

    def build_argparse(self, subparser):
        find_episode_parser = subparser.add_parser(self.name, help='Find Season/Episode/Part using file names',
                                                   parents=[parent_parser, input_parser])

        find_episode_parser.add_argument('--strip-youtube-dl', default=True, type=bool)
        find_episode_parser.add_argument('--concat-files', action='store_const', const=True, default=False)
        find_episode_parser.add_argument('--output', '-o', default='./', dest='output')
        find_episode_parser.add_argument('--seasons', action='store_const', const=True, default=False,
                                         help='If renaming, moves files into season directories')
        find_episode_parser.add_argument('--ignore-parts', action='store_const', const=True, default=False)
        find_episode_parser.add_argument('--use-101-pattern', '--101', action='store_const', const=True, default=False,
                                         help='Use a \d\d\d pattern')

        group = find_episode_parser.add_mutually_exclusive_group()
        group.add_argument('--rename', action='store_const', const=True, default=False,
                           help='Renames the files using the season & episode if found')
        group.add_argument('--copy', action='store_const', const=True, default=False,
                           help='Copies the file with new name to output directory')

    def subexecute(self, ns):
        import os
        from media_management_scripts.support.episode_finder import find_episodes
        from media_management_scripts.utils import season_episode_name
        from media_management_scripts.support.concat_mp4 import concat_mp4
        from texttable import Texttable

        concat = {}
        input = ns['input']
        do_new_name = ns.get('rename', False) or ns.get('copy', False)
        out_dir = ns['output']
        ignore_parts = ns['ignore_parts']
        season_folders = ns.get('seasons', False)

        table = []
        # for ep in sorted(find_episodes(input, ns['strip_youtube_dl']), key=lambda x: (x.season, x.episode, x.part)):
        results = list(find_episodes(input, ns['strip_youtube_dl'], ns.get('use_101_pattern')))
        for ep in sorted(results):
            # for ep in find_episodes(input, ns['strip_youtube_dl']):
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
                out_file = os.path.join(season_f, new_name)
                table.append((ep.path, ep.season_episode, out_file))
            elif ep.season and ep.episode:
                table.append((ep.path, ep.season_episode, None))
            else:
                table.append((ep.path, None, None))
        columns = ('Original', 'Episode', 'New Path')
        if ns.get('rename', False):
            self._bulk_move(table, column_descriptions=columns, src_index=0, dest_index=2, print_table=True)
        elif ns.get('copy', False):
            self._bulk_copy(table, column_descriptions=columns, src_index=0, dest_index=2, print_table=True)
        else:
            self._bulk_print(table, column_descriptions=columns, src_index=0, dest_index=2)
        for key in concat:
            concats = sorted(concat[key])
            print('s{}e{}'.format(key[0], key[1]))
            for item in concats:
                print('   {} pt{}'.format(item.name, item.part))
            if ns['concat_files']:
                to_concat = [item.path for item in concats]
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


SubCommand.register(FindEpisodesCommand)
