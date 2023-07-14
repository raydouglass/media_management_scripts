import os
from media_management_scripts.utils import create_metadata_extractor
from media_management_scripts.convert import cut


def split_by_chapter(input, output_dir, chapters=4, initial_count=0):
    extractor = create_metadata_extractor()
    metadata = extractor.extract(input)

    num_chapters = len(metadata.chapters)
    if num_chapters % chapters != 0:
        raise Exception(
            "Cannot evenly split {} by {} - {} chapters".format(
                input, chapters, num_chapters
            )
        )
    count = initial_count
    for i in range(0, num_chapters, chapters):
        if i != 0:
            start = metadata.chapters[i].start_time
        else:
            start = None
        if i + chapters < num_chapters:
            end = metadata.chapters[i + chapters - 1].end_time
        else:
            end = None
        output_file = os.path.join(output_dir, "title{0:02d}.mkv".format(count))
        count += 1
        cut(input, output_file, start, end)
    return num_chapters // chapters
