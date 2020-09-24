import os
import json
from os.path import join, isdir

DATA_PATH = join("data", "data.json")
EMPTY_DATA_FILE = {
    "last_session": "",
    "timer_size": 180,
    "scramble_size": 26,
    "enable_inspection": True
}


def recreate_data_folder():
    os.mkdir("data")
    os.mkdir("data/sessions")


def data_folder_exists() -> bool:
    return isdir("data") and isdir(join("data", "sessions"))


def recreate_data_file():
    with open(DATA_PATH, "w") as file:
        json.dump(EMPTY_DATA_FILE, file, indent=2)
