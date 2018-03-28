import argparse
from media_management_scripts.support.encoding import DEFAULT_CRF, DEFAULT_PRESET, Resolution



parent_parser = argparse.ArgumentParser(add_help=False)
parent_parser.add_argument('--print-args', action='store_const', const=True, default=False)
parent_parser.add_argument('-n', '--dry-run', action='store_const', const=True, default=False)

input_parser = argparse.ArgumentParser(add_help=False)
input_parser.add_argument('input', help='Input directory')

output_parser = argparse.ArgumentParser(add_help=False)
output_parser.add_argument('output', help='Output target')
output_parser.add_argument('-y', '--overwrite', help='Overwrite output target if it exists', action='store_const',
                           default=False, const=True)

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
convert_parent_parser.add_argument('--scale', choices=[r.height for r in Resolution], default=None, help='Set the maximum height scale')

__all__ = ['parent_parser', 'input_parser', 'output_parser', 'convert_parent_parser']
