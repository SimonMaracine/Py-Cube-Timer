from __future__ import annotations

import enum
import dataclasses
import random
from typing import List, Union, Type


class _3x3x3Letter(enum.Enum):
    R = "R"
    L = "L"
    U = "U"
    D = "D"
    F = "F"
    B = "B"


class _Modifier(enum.Enum):
    NONE = ""
    PRIME = "'"
    TWO = "2"


@dataclasses.dataclass
class _3x3x3Move:
    basic_move: _3x3x3Letter
    modifier: _Modifier

    def combined(self) -> str:
        return self.basic_move.value + self.modifier.value

    def is_opposite(self, other: _3x3x3Move) -> bool:
        if self.basic_move == _3x3x3Letter.R:
            return other.basic_move == _3x3x3Letter.L
        elif self.basic_move == _3x3x3Letter.L:
            return other.basic_move == _3x3x3Letter.R
        elif self.basic_move == _3x3x3Letter.U:
            return other.basic_move == _3x3x3Letter.D
        elif self.basic_move == _3x3x3Letter.D:
            return other.basic_move == _3x3x3Letter.U
        elif self.basic_move == _3x3x3Letter.F:
            return other.basic_move == _3x3x3Letter.B
        elif self.basic_move == _3x3x3Letter.B:
            return other.basic_move == _3x3x3Letter.F


_ALL_3x3x3_BASIC_MOVES = [move for move in _3x3x3Letter]
_ALL_MODIFIERS = [modifier for modifier in _Modifier]


def generate_3x3x3_scramble() -> str:
    moves: List[_3x3x3Move] = []

    while len(moves) < 20:
        while True:
            code = _add_move(moves, _3x3x3Move)
            if code == 1:
                continue
            elif code == 0:
                break

    final = [move.combined() for move in moves]
    return " ".join(final)


class _4x4x4SpecificLetter(enum.Enum):
    Rw = "Rw"
    Uw = "Uw"
    Fw = "Fw"


@dataclasses.dataclass
class _4x4x4Move:
    basic_move: Union[_3x3x3Letter, _4x4x4SpecificLetter]
    modifier: _Modifier

    def combined(self) -> str:
        return self.basic_move.value + self.modifier.value

    def is_opposite(self, other: _4x4x4Move) -> bool:
        if self.basic_move == _3x3x3Letter.R or self.basic_move == _4x4x4SpecificLetter.Rw:
            return other.basic_move == _3x3x3Letter.L
        elif self.basic_move == _3x3x3Letter.L:
            return other.basic_move == _3x3x3Letter.R or other.basic_move == _4x4x4SpecificLetter.Rw
        elif self.basic_move == _3x3x3Letter.U or self.basic_move == _4x4x4SpecificLetter.Uw:
            return other.basic_move == _3x3x3Letter.D
        elif self.basic_move == _3x3x3Letter.D:
            return other.basic_move == _3x3x3Letter.U or other.basic_move == _4x4x4SpecificLetter.Uw
        elif self.basic_move == _3x3x3Letter.F or self.basic_move == _4x4x4SpecificLetter.Fw:
            return other.basic_move == _3x3x3Letter.B
        elif self.basic_move == _3x3x3Letter.B:
            return other.basic_move == _3x3x3Letter.F or other.basic_move == _4x4x4SpecificLetter.Fw

    def is_type_equal(self, other: _4x4x4Move) -> bool:
        if self.basic_move == _4x4x4SpecificLetter.Rw:
            return other.basic_move == _3x3x3Letter.R
        elif self.basic_move == _4x4x4SpecificLetter.Uw:
            return other.basic_move == _3x3x3Letter.U
        elif self.basic_move == _4x4x4SpecificLetter.Fw:
            return other.basic_move == _3x3x3Letter.F


_ALL_4x4x4_SPECIFIC_MOVES = [move for move in _4x4x4SpecificLetter]


def generate_4x4x4_scramble() -> str:
    moves: List[_4x4x4Move] = []

    moves_so_far = 0

    while len(moves) < 45:
        if moves_so_far < 20:
            while True:
                code = _add_move(moves, _4x4x4Move)
                if code == 1:
                    continue
                elif code == 0:
                    break
        else:
            move_type = random.choice((_3x3x3Move, _4x4x4Move))

            while True:
                if move_type == _3x3x3Move:
                    code = _add_move(moves, _4x4x4Move)
                    if code == 1:
                        continue
                    elif code == 0:
                        break
                else:
                    move = _4x4x4Move(random.choice(_ALL_4x4x4_SPECIFIC_MOVES), random.choice(_ALL_MODIFIERS))

                    if type(moves[-1].basic_move) == _4x4x4SpecificLetter:
                        if moves[-1].basic_move == move.basic_move:
                            continue
                    else:
                        if move.is_type_equal(moves[-1]):
                            continue

                    if moves[-1].is_opposite(move):
                        if type(moves[-2].basic_move) == _4x4x4SpecificLetter:
                            if moves[-2].basic_move == move.basic_move:
                                continue
                        else:
                            if move.is_type_equal(moves[-2]):
                                continue

                    moves.append(move)
                    break

        moves_so_far += 1

    final = [move.combined() for move in moves]
    return " ".join(final)


def _add_move(moves: List[Union[_3x3x3Move, _4x4x4Move]], move_type: Union[Type[_3x3x3Move], Type[_4x4x4Move]]) -> int:
    """
    Return 0 means break and return 1 means continue.

    """
    move = move_type(random.choice(_ALL_3x3x3_BASIC_MOVES), random.choice(_ALL_MODIFIERS))

    try:
        if moves[-1].basic_move == move.basic_move:
            return 1
    except IndexError:  # The list is empty now
        pass

    try:
        if moves[-1].is_opposite(move):
            if moves[-2].basic_move == move.basic_move:
                return 1
    except IndexError:  # The list is empty or it has only one element
        pass

    moves.append(move)
    return 0
