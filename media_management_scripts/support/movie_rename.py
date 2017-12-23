from media_management_scripts.moviedb import MovieDbApi, NameInformation
from shutil import move
from dialog import Dialog

from paramiko import Transport, RSAKey
import os
from difflib import SequenceMatcher
from scp import SCPClient
from media_management_scripts.support.formatting import sizeof_fmt
from media_management_scripts.utils import create_metadata_extractor

OK = 0
CANCEL = 1


def _transfer(result: NameInformation, input_file, username, pkey_file, host, output_path):
    output_file = os.path.join(output_path, os.path.basename(input_file))
    pkey = RSAKey.from_private_key_file(filename=pkey_file)
    with Transport((host, 22)) as transport:
        transport.connect(username=username, pkey=pkey)

        filename = os.path.basename(output_file)
        d = Dialog(autowidgetsize=False)
        d.gauge_start(title=result.simple_name, text='Transferring...\n{}'.format(filename),
                      percent=0)
        try:

            def callback(file, m, curr):
                current = sizeof_fmt(curr)
                max = sizeof_fmt(m)
                text = 'Transferring...\n{}\n{} of {}'.format(filename, current, max)
                d.gauge_update(percent=int(curr / m * 100), text=text, update_text=True)

            with SCPClient(transport, buff_size=2 * 1024 * 1024, progress=callback) as client:
                client.put(input_file, output_file)
        finally:
            d.gauge_stop()


def _search(title, file, metadata):
    results = MovieDbApi().search_title(title, metadata)
    # Sort by closeness to file's title, then title, then year
    if len(results) > 0:
        metadata_title = metadata.title if metadata.title is not None else ''
        results.sort(key=lambda x: (-SequenceMatcher(None, x.title, metadata_title).ratio(), x.title, x.year))
        choices = []
        for i in range(len(results)):
            choices.append((str(i), results[i].simple_name))
        d = Dialog(autowidgetsize=True)
        code, tag = d.menu('Choices:', choices=choices, title=os.path.basename(file))
        if code == d.OK:
            return OK, results[int(tag)]
        else:
            return CANCEL, None
    return OK, None


def _get_new_name(input_to_cmd) -> NameInformation:
    metadata = create_metadata_extractor().extract(input_to_cmd)
    result = None
    title = metadata.title
    if title:
        code, result = _search(title, input_to_cmd, metadata)
        if code == CANCEL:
            return None
    while result is None:
        title = ''
        d = Dialog(autowidgetsize=True)
        exit_code, title = d.inputbox('No matches found. Try a different title?', init=title,
                                      title=os.path.basename(input_to_cmd))
        if exit_code == d.OK:
            code, result = _search(title, input_to_cmd, metadata)
            if code == CANCEL:
                return None
        else:
            return None

    return result


def movie_rename(input_to_cmd, ns):
    dry_run = ns.get('dry_run', False)
    results = [(i, _get_new_name(i)) for i in input_to_cmd]
    if results:
        username = ns.get('username', None)
        host = ns.get('host', None)
        pkey_file = ns.get('pkey', None)
        output_path = ns.get('output_path', None)
        move_source = ns.get('move_source_path', None)
        for original, result in results:
            if result:
                new_file = result.new_name(original)
                if not dry_run:
                    if not host or not pkey_file or not output_path:
                        print('If not using dry-run, you must include the host, pkey, and output path')
                    else:
                        move(original, new_file)
                        _transfer(result, new_file, username, pkey_file, host, output_path)
                        if move_source:
                            new_loc = os.path.join(move_source, os.path.basename(new_file))
                            dir = os.path.dirname(new_file)
                            move(new_file, new_loc)
                            if len(os.listdir(dir)) == 0:
                                os.rmdir(dir)

                else:
                    print(new_file)
