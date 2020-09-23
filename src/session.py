import json
import dataclasses
import logging
import copy
from os.path import join, isfile
from typing import List, Optional
from math import inf

from src.data import DATA_PATH, recreate_data_file

_SESSIONS_PATH = join("data", "sessions")
_EMPTY_SESSION = {
    "name": "",
    "mean": "inf",
    "best_time": "inf",
    "best_ao5": "inf",
    "best_ao12": "inf",
    "solves": []
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


def dump_data(file_name: str, mean: str, best_time: str, best_ao5: str, best_ao12: str, solve: Solve = None):
    with open(join(_SESSIONS_PATH, file_name), "r+") as file:
        try:
            contents = json.load(file)
        except json.decoder.JSONDecodeError:
            logging.error(f'File "{file_name}" is corrupted')
            raise ValueError  # Let the caller handle this error

        file.seek(0)

        if solve is not None:
            contents["solves"].append(solve.__dict__)
        contents["mean"] = mean
        contents["best_time"] = best_time
        contents["best_ao5"] = best_ao5
        contents["best_ao12"] = best_ao12

        json.dump(contents, file, indent=2)
        file.truncate()


def remove_solve_out_of_session(file_name: str):
    with open(join(_SESSIONS_PATH, file_name), "r+") as file:
        try:
            contents = json.load(file)
        except json.decoder.JSONDecodeError:
            logging.error(f"File '{file_name}' is corrupted")
            raise ValueError  # Let the caller handle this error

        file.seek(0)

        logging.debug(f"Removing solve {contents['solves'][-1]}")
        del contents['solves'][-1]

        json.dump(contents, file, indent=2)
        file.truncate()  # Don't forget this!


# TODO make method to copy a session and rename it


def remember_last_session(name: str):  # TODO check for exceptions here and for missing entries!
    with open(DATA_PATH, "r+") as file:
        contents = json.load(file)

        file.seek(0)

        contents["last_session"] = name

        json.dump(contents, file, indent=2)
        file.truncate()


def get_last_session() -> str:
    try:
        with open(DATA_PATH, "r") as file:
            contents = json.load(file)
            assert contents["last_session"]
            return contents["last_session"]
    # Let the caller handle these errors
    except FileNotFoundError:
        recreate_data_file()
        logging.error("Data file was missing")
        raise
    except json.decoder.JSONDecodeError:
        recreate_data_file()
        logging.error("Data file was somehow corrupted")
        raise ValueError
    except AssertionError:
        logging.info("There is no last session")
        raise


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
