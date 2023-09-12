# Media Management Scripts

This is a collection of command line tools for managing media files such as movies or TV shows.

## Installation

Install the tools:

`pip install media_management_scripts`

You also need to install other programs:

### MacOS

`brew install ffmpeg dialog`

### Ubuntu

`apt install ffmpeg dialog`

### TVDB

If you want to use TVDB for some commands, create an account on <https://www.thetvdb.com> and create a legacy API key [here](https://www.thetvdb.com/dashboard/account/apikey)

Create a file `~/.config/tvdb/tvdb.ini` with contents:

```ini
[tvdb]
username = <your_user_name>
userkey = <your_user_key>
apikey = <your_api_key>
```

# Usage

Pass `--help` to the subcommands for detailed help. Major features are explained in detail below.

Most commands that rename or move files have a dry-run mode (`-n` or `--dry-run`) which will output the actions so you can verify the results.

## Main tools
__[convert](#convert)__

__[metadata](#metadata)__

__[rename](#rename)__

__[search](#search)__

__[tv-rename](#tv-rename)__


Help output
```
usage: manage-media [-h] [-v]

Sub commands
    combine-subtitles   Combine a video files with subtitle file
    combine-all         Combine a directory tree of video files with subtitle
                        file
    concat-mp4          Concat multiple mp4 files together
    convert             Convert a file
    find-episodes       Find Season/Episode/Part using file names
    itunes              Attempts to rename iTunes episodes to the standard
                        Plex format.
    metadata            Show metadata for a file
    compare             Compare metadata between files
    compare-directory   Show metadata for a file
    movie-rename        Renames a file based on TheMovieDB
    rename              Renames a set of files to the specified template
    select-streams      Extract specific streams in a video file to a new file
    split               Split a file
    subtitles           Convert subtitles to SRT
    tv-rename           Renames files in a directory to sXXeYY. Can also use
                        TVDB to name files (<show> - SxxeYY - <episode_name>)

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         Display version
```

## convert

`manage-media convert <input> <output>`

Convert a video file to different video or audio codecs. By default if no codecs are given, the file will be converted to H.264 with AAC audio.

The source file is left intact.

#### Examples:
- Convert to H.264
    - `manage-media convert --video-codec h264 <input> <output>`
- Convert to HEVC/H.265:
    - `manage-media convert --video-codec hevc <input> <output>`
- Convert to HEVC with AC3 audio:
    - `manage-media convert --video-codec hevc --audio-codec ac3 <input> <output>`
- Convert to HEVC, but don't convert audio:
    - `manage-media convert --vc hevc --ac copy <input> <output>`
- Scale to 480p
    - `manage-media convert --scale 480  <input> <output>`
- Convert to H.264 and remove interlacing (such as on mpeg2 DVDs)
    - `manage-media convert --vc h264 --deinterlace  <input> <output>`
- Convert a whole directory of files
    - `manage-media convert --vc h264 --bulk <input dir> <output dir>`
- Extract a portion of the video
    - `manage-media convert --vc copy --ac copy --start 3m45s --end 10m00s <input> <output>`

## metadata

Get a simple output of metadata for a file. Or get lots of metadata in json format

#### Simple output
`manage-media metadata <input>`
```
Battlestar Galatica (2003) - s00e01 - Battlestar Galactica The Miniseries (1).mkv
   Directory: /Volumes/Media/TV Shows/Battlestar Galactica/Season 0/
   Title: Battlestar Galactica: Season 1 (Disc 1)
   Size: 6.8GB
   Format: matroska,webm
   Duration: 1h34m39s
   Bitrate: 10117 Kbps
   Video: h264 8 bit (1920x1080)
   Audio:
     aac (eng, 5.1)
   Subtitles: eng, spa, fra
   Ripped: True
```

#### Json
`manage-media metadata --json <input>`
```json
{
  "file": "/Volumes/Media/TV Shows/Battlestar Galactica/Season 0/Battlestar Galatica (2003) - s00e01 - Battlestar Galactica The Miniseries (1).mkv",
  "title": "Battlestar Galactica: Season 1 (Disc 1)",
  "duration": 5679.362,
  "duration_str": "1h34m39s",
  "size": 7354722701,
  "size_str": "6.8GB",
  "resolution": "HIGH_DEF",
  "bit_rate": 10359928,
  "bit_rate_str": "10117 Kbps",
  "ripped": true,
  "format": "matroska,webm",
  "format_long_name": "Matroska / WebM",
  "mime_type": "video/x-matroska",
  "tags": {
    "title": "Battlestar Galactica: Season 1 (Disc 1)",
    "RIPPED": "true",
    "ENCODER": "Lavf57.56.100"
  },
  "video_streams": [ ... ],
  "audio_streams": [ ... ],
  "subtitle_streams": [ ... ],
  "other_streams": [ ... ],
  "chapters": [ ... ],
  "interlace": null
}
```

## rename

`manage-media rename <template> <input file>` or `manage-media rename --recursive <template> <input directory>`

A flexible tool to rename files

Rename files based on a template.

Templates can include variables or expressions by surrounding with ${...}. Functions can be called like `${upper(i)}` or `${i | upper}`.

The following variables are available:
  * `i`/`index` - The index of the current file being renamed
  * `wo_ext` - The file name basename without the extension
  * `ext` - The file extension of the current file (without '.')
  * `filename` - The filename of the current file (basename)
  * `re`/`regex` - A list of regex match groups (use `re[0]`, `re[1]`, etc)

The following functions are available:
  * `upper` - Upper cases the input
  * `lower` - Lower cases the input
  * `ifempty(a, b, c)` - If a is empty or null, then b, otherwise c
  * `lpad(a, b:int)` - Left pads a to length b (defaults to 2+) with spaces
  * `zpad(a, b:int)` - Left pads a to length b (defaults to 2+) with zeros

`lpad`/`zpad` - By default pads to at least 2 characters. If there are 100+ files, then 3 characters, 1000+ files, then 4 characters, etc.

Regular Expressions:
If a regex is included, the match groups (0=whole match, >0=match group) are available in a list 're' or 'regex'.
Each match group is converted to an int if possible, so a zero padded int will lose the zeros.

Example Templates:
```
Input: S02E04.mp4
Regex: S(\d+)E(\d+)

Template: 'Season ${re[1]} Episode ${re[2]}.{ext}'
Result: 'Season 2 Episode 4.mp4'

Template: 'Season ${re[1] | zpad} Episode ${zpad(re[2], 3)}.{ext}'
Results: 'Season 02 Episode 004.mp4'
```
```
Input: whatever.mp4
Regex: S(\d+)E(\d)
Template: 'Season ${ifempty(re[1], 'unknown', re[1])} Episode ${re[2]}.{ext}'
Result: 'Season unknown Episode .mp4'
```

## search

`manage-media search <input directory> <query>`

Searches a directory for video files matching parameters. Note: this can take a LONG time as it has to read the metadata for each file.
You can speed up multiple searches in the same directory with `--db <file` which caches the metadata.

If a video has multiple streams, comparisons mean at least one stream matches.

Available parameters:

Video:
- `v.codec` - The video codec (h264, h265, mpeg2, etc)
- `v.width` - The video pixel width
- `v.height` - The video pixel height

Audio:
- `a.codec` - The audio codec (aac, ac3)
- `a.channels` - The number of audio channels (stereo=2, 5.1=6, etc)
- `a.lang` - The language of the audio track

Subtitles:
- `s.codec` - The subtitle codec (srt, hdmv_pgs, mov_text, etc)
- `s.lang` - The language of the subtitle track

Others:
- `ripped` - Whether the video is marked as ripped or not
- `bit_rate` - The overall average bitrate
- `resolution` - The resolution name (LOW_DEF, HIGH_DEF, etc)

Metadata:
- `meta.xyz` - Follows the basic JSON metadata output

Functions:
- `isNull(xyz)` - Returns true if the value is null
- `all(xyz)` - Instead of one stream matching, check all of them

Example Queries:
- Find all videos that are H264
    - `v.codec = h264`
- Find all videos that are H264 with stereo AAC
    - `v.codec = h264 and a.codec = aac and a.channels = 2`
- Find all videos that are H265 or H264 and AAC
    - `a.codec = aac and (v.codec = h265 or v.codec = h264)`
    - `a.codec = aac and v.codec in [h265, h264]`
- Find all videos without English Subtitles
    - `s.lang != eng`
- Find videos that are lower resolution than 1080
    - `v.height < 1080`
- Find all videos that have ONLY AAC audio
    - `all(a.codec) = aac`

## tv-rename

Renames files in a directory to sXXeYY

For example, if you ripped some Battlestar Galactica blurays, you might have a file structure like:

- BSG_Season1_Disc1
    - BSG_Season1_Disc1_t00.mkv
    - BSG_Season1_Disc1_t01.mkv
    - BSG_Season1_Disc1_t02.mkv
    - BSG_Season1_Disc1_t03.mkv
- BSG_Season1_Disc2
    - BSG_Season1_Disc2_t00.mkv
    - BSG_Season1_Disc2_t01.mkv
    - BSG_Season1_Disc2_t02.mkv
    - BSG_Season1_Disc2_t03.mkv

`manage-media tv-rename -s 1 -e 1 --tvdb --show "Battlestar Galactica" --output "BSG/Season 1" BSG_Season1_Disc*`

Result
- BSG
    - Season 1
        - Battlestar Galatica (2003) - S01E01 - 33.mkv
        - Battlestar Galatica (2003) - S01E02 - Water.mkv
        - Battlestar Galatica (2003) - S01E03 - Bastille Day.mkv
        - Battlestar Galatica (2003) - S01E04 - Act of Contrition.mkv
        - Battlestar Galatica (2003) - S01E05 - You Can't Go Home Again.mkv
        - Battlestar Galatica (2003) - S01E06 - Litmus.mkv
        - Battlestar Galatica (2003) - S01E07 - Six Degrees of Separation.mkv
        - Battlestar Galatica (2003) - S01E08 - Flesh and Bone.mkv


## Configuration

You can configuration where to find various executables by creating a file `~/.config/mms/config.ini`. By default, commands will use the executables found in your path.

You can see which tools are being used with `manage-media `

Config File Example
```ini
[main]
ffmpeg = /path/to/ffmpeg

```
