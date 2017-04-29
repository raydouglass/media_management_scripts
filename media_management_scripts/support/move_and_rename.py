from media_management_scripts.moviedb import MovieDbApi
from paramiko.sftp_client import SFTPClient
from paramiko import Transport, PKey
import os


def confirm_new_name(input_file):
    results = MovieDbApi().search_file(input_file, single_result=False)
    choice = None
    while not choice:
        print('Choose:')
        index = 1
        for r in results:
            print('  {}) {}'.format(index, r.name))
            index += 1
        choice = input('Selection (q to quit): ')
        if choice == 'q':
            return None
        try:
            choice = int(choice)
            if choice < 1 or choice > len(results):
                choice = None
        except ValueError:
            choice = None
    return results[choice - 1]


def rename(input_file):
    name_info = confirm_new_name(input_file)
    if name_info:
        return name_info.new_name(input_file)
    else:
        return None


def rename_and_move(input_file, pkey_file, host, output_path, transferred_dir):
    new_path = rename(input_file)
    if not new_path:
        return None

    pkey = PKey.from_private_key_file(pkey_file)
    transport = Transport((host, 22))
    transport.connect(pkey=pkey)

    client = SFTPClient.from_transport(transport)
    client.put(new_path, output_path)

    dest = os.path.json(transferred_dir, os.path.basename(new_path))
    os.rename(new_path, dest)




