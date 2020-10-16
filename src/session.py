import json
import dataclasses
import logging
import copy
import os
import shutil
import datetime
from os.path import join, isfile
from typing import List, Optional

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
    raw_time: float  # In seconds


@dataclasses.dataclass
class SessionData:
    name: str
    solves: List[Solve]  # Solve times can sometimes contain only one decimal
    all_ao5: List[float]
    all_ao12: List[float]


class FileCorruptedError(json.decoder.JSONDecodeError):
    pass


class SameFileError(shutil.SameFileError):
    pass


def create_new_session(name: str, check_first: bool) -> SessionData:
    if check_first:
        if isfile(join(_SESSIONS_PATH, name + ".json")):
            raise FileExistsError

    with open(join(_SESSIONS_PATH, name + ".json"), "w") as file:
        data = copy.copy(_EMPTY_SESSION)
        data["name"] = name
        json.dump(data, file, indent=2)

    return SessionData(name, [], [], [])


def dump_data(file_name: str, solve: Solve):
    with open(join(_SESSIONS_PATH, file_name), "r+") as file:
        try:
            contents = json.load(file)
        except json.decoder.JSONDecodeError:
            logging.error(f'File "{file_name}" is corrupted')
            raise FileCorruptedError  # Let the caller handle this error

        file.seek(0)

        dictionary = copy.copy(solve.__dict__)
        del dictionary["raw_time"]  # Don't dump raw_time
        contents["solves"].append(dictionary)

        json.dump(contents, file, indent=2)
        file.truncate()


def remove_solve_out_of_session(file_name: str):
    with open(join(_SESSIONS_PATH, file_name), "r+") as file:
        try:
            contents = json.load(file)
        except json.decoder.JSONDecodeError:
            logging.error(f'File "{file_name}" is corrupted')
            raise FileCorruptedError  # Let the caller handle this error

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
    except FileNotFoundError:
        logging.error(f"Could not rename session; file {source} not found")
        raise

    with open(destination, "r+") as file:
        contents = json.load(file)

        file.seek(0)

        contents["name"] = destination_name
        json.dump(contents, file, indent=2)
        file.truncate()


def destroy_session(name: str):
    try:
        os.remove(join(_SESSIONS_PATH, name + ".json"))
    except FileNotFoundError:
        logging.error(f"Could not remove session; file {name}.json not found")
        raise


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
        logging.error("Data file was missing")
        recreate_data_file()
        raise
    except json.decoder.JSONDecodeError:
        logging.error("Data file was somehow corrupted")
        recreate_data_file()
        raise FileCorruptedError


def get_last_session() -> str:
    try:
        with open(DATA_PATH, "r") as file:
            contents = json.load(file)
            if not contents["last_session"]:
                raise RuntimeError
            return contents["last_session"]
    # Let the caller handle these errors
    except FileNotFoundError:
        logging.error("Data file was missing")
        recreate_data_file()
        raise
    except json.decoder.JSONDecodeError:
        logging.error("Data file was somehow corrupted")
        recreate_data_file()
        raise FileCorruptedError
    except RuntimeError:
        logging.info("There is no last session")
        raise
    except KeyError as err:
        logging.error(f"Missing entry: {err}")
        recreate_data_file()
        raise


def load_session_data(file_name: str) -> Optional[SessionData]:
    try:
        with open(join(_SESSIONS_PATH, file_name), "r") as file:
            contents = json.load(file)
    except FileNotFoundError:
        logging.error(f"Could not find file {file_name}")
        return None
    except json.decoder.JSONDecodeError:
        logging.error(f"{file_name} is corrupted")
        return None

    try:
        name = contents["name"]
        # Solve times can sometimes contain only one decimal
        solves: List[Solve] = [Solve(time=solve["time"], scramble=solve["scramble"], date=solve["date"],
                                     raw_time=interpret_time_in_seconds(solve["time"])) for solve in contents["solves"]]
        assert name
    except KeyError as err:  # Missing contents
        logging.error(f"Missing entry: {err}")
        return None
    else:
        return SessionData(name, solves, [], [])


def session_exists(name: str) -> bool:
    return isfile(join(_SESSIONS_PATH, name + ".json"))


def backup_session(session_file: str, folder_path: str):
    date = datetime.datetime.now().date()

    source = join(_SESSIONS_PATH, session_file)
    destination = join(folder_path, "backup_" + f"{date.year}-{date.month}" + "_" + session_file)

    try:
        shutil.copyfile(source, destination)
    except FileNotFoundError:
        logging.error(f"Could not find file {source}")
        raise
    except shutil.SameFileError:  # TODO maybe we should prevent this completely instead of catching it
        logging.error(f"Cannot backup in the sessions folder")
        raise SameFileError
    except OSError:
        logging.error(f"Could not backup file {source}, because the destination is not writable (permission denied)")
        raise
