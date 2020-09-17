import json
import dataclasses
from os.path import join

SESSIONS_PATH = join("data", "sessions")
EMPTY_SESSION = {
    "name": "",
    "mean": 0.0,
    "best_time": 0.0,
    "best_ao5": 0.0,
    "best_ao12": 0.0,
    "times": []
}


@dataclasses.dataclass
class Time:
    time: float
    scramble: str
    date: str


def create_new_session(name: str):
    with open(join(SESSIONS_PATH, name), "r+") as file:
        json.dump(EMPTY_SESSION, file, indent=2)


def dump_data(file_name: str, time: Time = None, name: str = None, best_time: float = None, best_ao5: float = None,
              best_ao12: float = None):
    with open(join(SESSIONS_PATH, file_name), "r+") as file:
        contents = json.load(file)

        file.flush()
        file.seek(0)

        if time is not None:
            contents["times"].append(time.__dict__)
        if name is not None:
            contents["name"] = name
        if best_time is not None:
            contents["best_time"] = best_time
        if best_ao5 is not None:
            contents["best_ao5"] = best_ao5
        if best_ao12 is not None:
            contents["best_ao12"] = best_ao12

        json.dump(contents, file, indent=2)


# create_new_session("test")
dump_data("test.json", Time(12.76, "a long WCA scramble", "17.09.2020"))
