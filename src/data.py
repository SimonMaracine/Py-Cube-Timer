import os
import json
from os.path import join, isdir

from src.timer import DEFAULT_READY_COLOR, DEFAULT_INSPECTION_COLOR

DATA_PATH = join("data", "data.json")
DEFAULT_BACKGROUND_COLOR = "#f0f0ed"
DEFAULT_TIMER_SIZE = 120
DEFAULT_SCRAMBLE_SIZE = 28

_EMPTY_DATA_FILE = {
    "last_session": "",
    "timer_size": DEFAULT_TIMER_SIZE,
    "scramble_size": DEFAULT_SCRAMBLE_SIZE,
    "enable_inspection": True,
    "background_color": DEFAULT_BACKGROUND_COLOR,
    "foreground_color": "#000000",
    "enable_backup": False,
    "backup_path": "",
    "ready_color": DEFAULT_READY_COLOR,
    "inspection_color": DEFAULT_INSPECTION_COLOR
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
