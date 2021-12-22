import requests
import json
import time
import os
import sys
import youtube_dl
from os.path import exists

base_url_yt_api = "https://youtube.googleapis.com/youtube/v3"
base_url_last_fm_api = "https://ws.audioscrobbler.com/2.0"
base_url_yt_videos = "https://www.youtube.com/watch?v="

# TODO: add ability to create song_names.txt from given directory


class Config:
    def __init__(self, args: list[str]):

        if len(args) != 3:
            print("ERROR: Wrong number or arguments.")
            print("Usage: " + args[0] +
                  " <path/to/config> <path/to/music-folder>")
            exit(1)

        self.path_to_music_folder = args[2]

        with open(args[1]) as f:
            config_file = json.loads(f.read())
            self.yt_api_key = config_file["ytApiKey"]
            self.last_fm_api_key = config_file["lastFmApiKey"]
            self.playlist_id = config_file["playlistId"]

# TODO: find a way (maybe different API?) to get get info about genres/album


class SongInfo:
    def __init__(self, data: dict[str, str]):
        self.title = data["snippet"]["title"]
        self.artist = data["snippet"]["videoOwnerChannelTitle"]
        self.video_id = data["snippet"]["resourceId"]["videoId"]

    def __str__(self):
        return "[ title: " + str(self.title) + ", artist: " + str(self.artist) + ", video_id:" + str(self.video_id) + "]"

    def __repr__(self):
        return self.__str__()

    # TODO: if youtube name is of type "artist - song_name", (or similar),
    # TODO: use this information in searching (or set them as default?)
    def add_song_meta_data(self, config: Config) -> None:

        parameter = {"format": "json",
                     "limit": 1,
                     "api_key": config.last_fm_api_key,
                     "track": self.title
                     }

        r = requests.get(base_url_last_fm_api +
                         "/?method=track.search", params=parameter)
        req_json = r.json()

        if len(req_json["results"]["trackmatches"]["track"]) > 0:
            first_song_info = req_json["results"]["trackmatches"]["track"][0]
            self.artist = first_song_info["artist"]
        else:
            print("WARNING: Song: \"" + self.title +
                  "\" Could not be found in the metadata-database.")
            print("WARNING: Using youtube-data: video-title and channel-name")


def get_song_names(config: Config) -> list[SongInfo]:
    print("Syncing with playlist...")
    parameter = {"playlistId": config.playlist_id,
                 "key": config.yt_api_key,
                 "maxResults": 50}

    song_names = []

    r = requests.get(
        base_url_yt_api + "/playlistItems?part=snippet", params=parameter)

    req_json = r.json()

    while True:

        for item in req_json["items"]:
            song_names.append(SongInfo(item))

        if "nextPageToken" in req_json:
            parameter["pageToken"] = req_json["nextPageToken"]
        else:
            break

        r = requests.get(base_url_yt_api, params=parameter)
        req_json = r.json()

    return song_names


def get_change(song_names_old: list[str], song_names: list[SongInfo]) -> tuple[list[SongInfo], list[str]]:

    print("Calculating changes...")

    current_song_names = list(map(lambda x: x.title, song_names))

    removed_songs = list(set(song_names_old) - set(current_song_names))

    added_songs = list(
        filter(lambda x: x.title not in song_names_old, song_names))

    return (added_songs, removed_songs, len(added_songs) + len(removed_songs) > 0)


def remove_songs(song_names: list[str], config: Config):

    if len(song_names) != 0:
        print(
            f"Removing songs from given music-directory: {config.path_to_music_folder}")

        for song_name in song_names:
            try:
                os.remove(os.path.expanduser(
                    config.path_to_music_folder + "/" + song_name + ".mp3"))
            except:
                print(f"ERROR: Unable to find song-file \"{song_name}.mp3\"")


def download_songs(song_infos: list[SongInfo], config: Config):

    if len(song_infos) == 0:
        return

    print(f"Downloading new songs...")

    for song_info in song_infos:

        ydl_opts = {
            'postprocessors': [{
                'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'
            }],
            'outtmpl': f"{os.path.expanduser(config.path_to_music_folder)}/{song_info.title}.%(ext)s",
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([base_url_yt_videos + song_info.video_id])


def save_new_song_names(song_infos: list[SongInfo], config: Config):

    print("Saving new song_names.txt...")

    names = ""

    for name in list(map(lambda x: x.title, song_infos)):
        names += name + "\n"

    names = names[:-1]

    with open(f"{config.path_to_music_folder}/song_names.txt", "w") as song_file:
        song_file.write(names)


def inject_infos_into_mp3s(song_infos: list[SongInfo], config: Config) -> None:
    if len(song_infos) == 0:
        return
    print("Adding mp3-meta-data to given songs...")
    pass


def load_song_names_old(config: Config) -> list[str]:

    song_names_old = []

    print("Loading song_names.txt...")
    if exists(f"{config.path_to_music_folder}/song_names.txt"):
        song_names_old = open(
            f"{config.path_to_music_folder}/song_names.txt").read().split('\n')
    else:
        print("WARNING: Unable to find the cached song_names.txt")
        print("Proceeding to view complete playlist as \"newly added\"...")

    return list(filter(lambda x: len(x) > 0, song_names_old))


def add_meta_data_to_songs(song_infos: list[SongInfo], config: Config) -> None:
    if len(song_infos) == 0:
        return

    print(f"Adding meta-data using last-fm API to newly added songs...")
    for song_info in song_infos:
        song_info.add_song_meta_data(config)

    time.sleep(5)


config = Config(sys.argv)

song_infos = get_song_names(config)

song_names_old = load_song_names_old(config)

(added_songs, removed_songs, there_was_change) = get_change(
    song_names_old, song_infos)

if not there_was_change:
    print("List up to date. Nothing to be done.")
    exit(0)

print(
    f"Found {len(added_songs)} \"newly added\" and {len(removed_songs)} \"removed\" songs.")

remove_songs(removed_songs, config)
download_songs(added_songs, config)
add_meta_data_to_songs(added_songs, config)
inject_infos_into_mp3s(added_songs, config)
save_new_song_names(song_infos, config)
