# (Y)ou(t)ube (p)lay(l)ist (s)yncer

This is a simple script that keeps a given directory up-to-date to a youtube playlist. This only works for songs right now, as the script downloads and keeps the mp3's (however, adding support for full videos is trivial)
- newly added songs will be downloaded
- removed songs will be deleted

After downloading the newly added songs, This script will connect to the last-FM API to gain meta-data information about the song (such as artist, album etc) and add these to the given mp3.

## You need
- Python 3 (dependencies in Pipfile)
- an youtube-API key
- a last-FM API key

## config
The config.json file looks like this:
```
{
    "ytApiKey": "<your-yt-api-key>",
    "lastFmApiKey": "<your-last-fm-api-key>",
    "playlistId": "<your-yt-playlist-id>",
}
```

## Invokation
```
python3 ytpls.py <path/to/config> <path/to/music/directory>
```