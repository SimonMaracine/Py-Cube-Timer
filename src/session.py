import json
import dataclasses
import logging
import copy
from os.path import join, isfile
from typing import List, Optional
from math import inf

_SESSIONS_PATH = join("data", "sessions")
_EMPTY_SESSION = {
    "name": "",
    "mean": "inf",
    "best_time": "inf",
    "best_ao5": "inf",
    "best_ao12": "inf",
    "solves": []
}
_EMPTY_DATA_FILE = {
    "last_session": ""
}


@dataclasses.dataclass
class Solve:
    time: float
    scramble: str
    date: str


@dataclasses.dataclass
class SessionData:
    name: str
    mean: float
    best_time: float
    best_ao5: float
    best_ao12: float
    solves: List[float]  # Solve times can sometimes contain only one decimal


def create_new_session(name: str) -> SessionData:
    with open(join(_SESSIONS_PATH, name + ".json"), "w") as file:
        data = copy.copy(_EMPTY_SESSION)
        data["name"] = name
        json.dump(data, file, indent=2)

    return SessionData(name, inf, inf, inf, inf, [])


def dump_data(file_name: str, solve: Solve = None, mean: str = None, best_time: str = None, best_ao5: str = None,
              best_ao12: str = None):
    with open(join(_SESSIONS_PATH, file_name), "r+") as file:
        contents = json.load(file)

        file.seek(0)

        if solve is not None:
            contents["solves"].append(solve.__dict__)
        if mean is not None:
            contents["mean"] = mean
        if best_time is not None:
            contents["best_time"] = best_time
        if best_ao5 is not None:
            contents["best_ao5"] = best_ao5
        if best_ao12 is not None:
            contents["best_ao12"] = best_ao12

        json.dump(contents, file, indent=2)


# TODO make method to copy a session and rename it


def _recreate_data_file():
    with open(join("data", "data.json"), "w") as file:
        json.dump(_EMPTY_DATA_FILE, file, indent=2)


def remember_last_session(name: str):
    with open(join("data", "data.json"), "r+") as file:
        contents = json.load(file)

        file.seek(0)

        contents["last_session"] = name
        json.dump(contents, file, indent=2)


def get_last_session() -> str:
    try:
        with open(join("data", "data.json"), "r") as file:
            contents = json.load(file)
            assert contents["last_session"]
            return contents["last_session"]
    except FileNotFoundError:
        _recreate_data_file()
        raise
    except json.decoder.JSONDecodeError:
        raise  # TODO should recreate data file here too
    except AssertionError:
        logging.info("There is no last session")
        raise  # Let the caller handle the error


def load_session_data(file_name: str) -> Optional[SessionData]:
    try:
        with open(join(_SESSIONS_PATH, file_name), "r") as file:
            contents = json.load(file)
    except FileNotFoundError as err:
        logging.error(err)
        return None
    except json.decoder.JSONDecodeError as err:
        logging.error(err)
        return None

    try:
        name = contents["name"]
        mean = float(contents["mean"])
        best_time = float(contents["best_time"])
        best_ao5 = float(contents["best_ao5"])
        best_ao12 = float(contents["best_ao12"])
        solves = [solve["time"] for solve in contents["solves"]]  # Solve times can sometimes contain only one decimal

        assert name
    except KeyError as err:  # Missing contents
        logging.error(f"Missing entry: {err}")
        return None
    else:
        return SessionData(name, mean, best_time, best_ao5, best_ao12, solves)


def session_exists(name: str) -> bool:
    return isfile(join(_SESSIONS_PATH, name + ".json"))
