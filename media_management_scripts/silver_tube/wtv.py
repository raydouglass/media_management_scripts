import os
from media_management_scripts.utils import create_metadata_extractor

ORIGINAL_BROADCAST_DATE_KEY = 'WM/MediaOriginalBroadcastDateTime'


def extract_original_air_date(wtv_file, parse_from_filename=True, metadata=None):
    if metadata is None:
        metadata = create_metadata_extractor().extract(wtv_file)
    # WM/MediaOriginalBroadcastDateTime=2012-10-13T04:00:00Z
    air_date = None

    if ORIGINAL_BROADCAST_DATE_KEY in metadata.tags:
        air_date = metadata.tags[ORIGINAL_BROADCAST_DATE_KEY]
    if air_date is None or air_date == '0001-01-01T00:00:00Z':
        # Extract from filename
        if parse_from_filename:
            split = os.path.basename(wtv_file).split('_')
            air_date = split[2] + '-' + split[3] + '-' + split[4]
        else:
            air_date = None
    else:
        air_date = air_date.split('T')[0]
    return air_date
