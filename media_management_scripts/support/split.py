import os
from media_management_scripts.utils import create_metadata_extractor
from media_management_scripts.convert_dvd import cut


def split_by_chapter(input, output_dir, number_of_pieces=4):
    extractor = create_metadata_extractor()
    metadata = extractor.extract(input)

    num_chapters = len(metadata.chapters)
    if num_chapters % number_of_pieces != 0:
        raise Exception('Cannot evenly split by {} - {} chapters'.format(number_of_pieces, num_chapters))
    step = num_chapters // number_of_pieces
    count = 0
    for i in range(0, num_chapters, step):
        if i != 0:
            start = metadata.chapters[i].start_time
        else:
            start = None
        if i + step < num_chapters:
            end = metadata.chapters[i + step-1].end_time
        else:
            end = None
        output_file = os.path.join(output_dir, 'title{0:02d}.mkv'.format(count))
        count += 1
        cut(input, output_file, start, end)
