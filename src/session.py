import json
import dataclasses
from os.path import join
from typing import List
from math import inf

_SESSIONS_PATH = join("data", "sessions")
_EMPTY_SESSION = {
    "name": "",
    "mean": inf,
    "best_time": inf,
    "best_ao5": inf,
    "best_ao12": inf,
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
    # mean: float
    solves: List[float]
    best_time: float
    best_ao5: float
    best_ao12: float


def create_new_session(file_name: str):
    with open(join(_SESSIONS_PATH, file_name), "w") as file:
        json.dump(_EMPTY_SESSION, file, indent=2)


def dump_data(file_name: str, solve: Solve = None, mean: str = None, name: str = None, best_time: str = None,
              best_ao5: str = None, best_ao12: str = None):
    with open(join(_SESSIONS_PATH, file_name), "r+") as file:
        contents = json.load(file)

        file.seek(0)

        if solve is not None:
            contents["solves"].append(solve.__dict__)
        if mean is not None:
            contents["mean"] = mean
        if name is not None:
            contents["name"] = name
        if best_time is not None:
            contents["best_time"] = best_time
        if best_ao5 is not None:
            contents["best_ao5"] = best_ao5
        if best_ao12 is not None:
            contents["best_ao12"] = best_ao12

        json.dump(contents, file, indent=2)


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
    except (json.decoder.JSONDecodeError, OSError):
        _recreate_data_file()
        # return

    # TODO handle case when there is no last session


def load_session_data(file_name: str) -> SessionData:
    with open(join(_SESSIONS_PATH, file_name), "r") as file:
        contents = json.load(file)

    # mean = float(contents["mean"])
    best_time = float(contents["best_time"])
    best_ao5 = float(contents["best_ao5"])
    best_ao12 = float(contents["best_ao12"])
    solves = [solve["time"] for solve in contents["solves"]]
    print(solves)

    return SessionData(contents["name"], solves, best_time,
                       best_ao5, best_ao12)
