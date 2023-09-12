from media_management_scripts.moviedb import MovieDbApi, NameInformation
from shutil import move
from dialog import Dialog

import os
from difflib import SequenceMatcher
from media_management_scripts.support.formatting import sizeof_fmt
from media_management_scripts.utils import create_metadata_extractor

OK = 0
CANCEL = 1


def _search(title, file, metadata):
    results = MovieDbApi().search_title(title, metadata)
    # Sort by closeness to file's title, then title, then year
    if len(results) > 0:
        metadata_title = metadata.title if metadata.title is not None else ""
        results.sort(
            key=lambda x: (
                -SequenceMatcher(None, x.title, metadata_title).ratio(),
                x.title,
                x.year,
            )
        )
        choices = []
        for i in range(len(results)):
            choices.append((str(i), results[i].simple_name))
        d = Dialog(autowidgetsize=True)
        code, tag = d.menu("Choices:", choices=choices, title=os.path.basename(file))
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
        title = ""
        d = Dialog(autowidgetsize=True)
        exit_code, title = d.inputbox(
            "No matches found. Try a different title?",
            init=title,
            title=os.path.basename(input_to_cmd),
        )
        if exit_code == d.OK:
            code, result = _search(title, input_to_cmd, metadata)
            if code == CANCEL:
                return None
        else:
            return None

    return result


def movie_rename(input_to_cmd, ns):
    dry_run = ns.get("dry_run", False)
    results = [(i, _get_new_name(i)) for i in input_to_cmd]
    if results:
        for original, result in results:
            if result:
                new_file = result.new_name(original)
                if not dry_run:
                    move(original, new_file)
                else:
                    print(new_file)
