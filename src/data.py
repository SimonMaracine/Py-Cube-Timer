import os
import json
from os.path import join, isdir

DATA_PATH = join("data", "data.json")
_EMPTY_DATA_FILE = {
    "last_session": "",
    "timer_size": 180,
    "scramble_size": 26,
    "enable_inspection": True,
    "background_color": [240, 240, 237],
    "foreground_color": [0, 0, 0]
}


def recreate_data_folder():
    try:
        os.mkdir("data")
    except FileExistsError:
        pass
    try:
        os.mkdir("data/sessions")
    except FileExistsError:  # Just to be sure...
        pass


def data_folder_exists() -> bool:
    return isdir("data") and isdir(join("data", "sessions"))


def recreate_data_file():
    with open(DATA_PATH, "w") as file:
        json.dump(_EMPTY_DATA_FILE, file, indent=2)
