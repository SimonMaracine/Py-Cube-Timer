import json
import dataclasses
from os.path import join

_SESSIONS_PATH = join("data", "sessions")
_EMPTY_SESSION = {
    "name": "",
    "mean": 0.0,
    "best_time": 0.0,
    "best_ao5": 0.0,
    "best_ao12": 0.0,
    "solves": []
}


@dataclasses.dataclass
class _Solve:
    time: float
    scramble: str
    date: str


@dataclasses.dataclass
class BestTimes:
    best_time: float
    best_ao5: float
    best_ao12: float


def create_new_session(name: str):
    with open(join(_SESSIONS_PATH, name), "w") as file:
        json.dump(_EMPTY_SESSION, file, indent=2)


def dump_data(file_name: str, solve: _Solve = None, name: str = None, best_time: float = None, best_ao5: float = None,
              best_ao12: float = None):
    with open(join(_SESSIONS_PATH, file_name), "r+") as file:
        contents = json.load(file)

        file.seek(0)

        if solve is not None:
            contents["solves"].append(solve.__dict__)
        if name is not None:
            contents["name"] = name
        if best_time is not None:
            contents["best_time"] = best_time
        if best_ao5 is not None:
            contents["best_ao5"] = best_ao5
        if best_ao12 is not None:
            contents["best_ao12"] = best_ao12

        json.dump(contents, file, indent=2)


# create_new_session("test.json")
# dump_data("test.json", solve=Solve(12.76, "a long WCA scramble", "17.09.2020"), name="Test session", best_time=7.39)
