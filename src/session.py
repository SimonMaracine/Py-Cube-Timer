import json
import dataclasses
import logging
import copy
import os
from os.path import join, isfile
from typing import List, Optional
from math import inf

from src.data import DATA_PATH, recreate_data_file
from src.timer import interpret_time_in_seconds

_SESSIONS_PATH = join("data", "sessions")
_EMPTY_SESSION = {
    "name": "",
    # All these times are formatted
    "solves": []
}


@dataclasses.dataclass
class Solve:
    time: str  # Formatted time
    scramble: str
    date: str


@dataclasses.dataclass
class SessionData:
    name: str
    solves: List[float]  # Solve times can sometimes contain only one decimal


def create_new_session(name: str) -> SessionData:
    with open(join(_SESSIONS_PATH, name + ".json"), "w") as file:
        data = copy.copy(_EMPTY_SESSION)
        data["name"] = name
        json.dump(data, file, indent=2)

    return SessionData(name, [])


def dump_data(file_name: str, solve: Solve):
    with open(join(_SESSIONS_PATH, file_name), "r+") as file:
        try:
            contents = json.load(file)
        except json.decoder.JSONDecodeError:
            logging.error(f'File "{file_name}" is corrupted')
            raise ValueError  # Let the caller handle this error

        file.seek(0)

        contents["solves"].append(solve.__dict__)

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
        del contents["solves"][-1]

        json.dump(contents, file, indent=2)
        file.truncate()  # Don't forget this!


def rename_session(source_name: str, destination_name: str):
    source = join(_SESSIONS_PATH, source_name + ".json")
    destination = join(_SESSIONS_PATH, destination_name + ".json")

    try:
        os.rename(source, destination)
    except FileNotFoundError as err:
        logging.error(err)
        raise

    with open(destination, "r+") as file:
        contents = json.load(file)

        file.seek(0)

        contents["name"] = destination_name
        json.dump(contents, file, indent=2)
        file.truncate()


def destroy_session(name: str):
    os.remove(join(_SESSIONS_PATH, name + ".json"))


def remember_last_session(name: str):
    try:
        with open(DATA_PATH, "r+") as file:
            contents = json.load(file)

            file.seek(0)

            contents["last_session"] = name

            json.dump(contents, file, indent=2)
            file.truncate()
    # Let the caller handle these errors
    except FileNotFoundError:
        recreate_data_file()
        logging.error("Data file was missing")
        raise
    except json.decoder.JSONDecodeError:
        recreate_data_file()
        logging.error("Data file was somehow corrupted")
        raise ValueError


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
    except KeyError as err:
        recreate_data_file()
        logging.error(f"Missing entry: {err}")
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
        # Solve times can sometimes contain only one decimal
        solves: List[float] = [interpret_time_in_seconds(solve["time"]) for solve in contents["solves"]]

        assert name
    except KeyError as err:  # Missing contents
        logging.error(f"Missing entry: {err}")
        return None
    else:
        return SessionData(name, solves)


def session_exists(name: str) -> bool:
    return isfile(join(_SESSIONS_PATH, name + ".json"))
