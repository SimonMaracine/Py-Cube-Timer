from __future__ import annotations

import enum
import dataclasses
import random
from typing import List


class _BasicMove(enum.Enum):
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
class _Move:
    basic_move: _BasicMove
    modifier: _Modifier

    def combined(self) -> str:
        return self.basic_move.value + self.modifier.value

    def is_opposite(self, other: _Move) -> bool:
        if self.basic_move == _BasicMove.R:
            return other.basic_move == _BasicMove.L
        elif self.basic_move == _BasicMove.L:
            return other.basic_move == _BasicMove.R
        elif self.basic_move == _BasicMove.U:
            return other.basic_move == _BasicMove.D
        elif self.basic_move == _BasicMove.D:
            return other.basic_move == _BasicMove.U
        elif self.basic_move == _BasicMove.F:
            return other.basic_move == _BasicMove.B
        elif self.basic_move == _BasicMove.B:
            return other.basic_move == _BasicMove.F


_ALL_BASIC_MOVES = [move for move in _BasicMove]
_ALL_MODIFIERS = [modifier for modifier in _Modifier]


def generate_scramble() -> str:
    moves: List[_Move] = []

    while len(moves) < 20:
        _append_move(moves)

    final = [move.combined() for move in moves]
    return " ".join(final)


def _append_move(moves: List[_Move]):
    while True:
        move = _Move(random.choice(_ALL_BASIC_MOVES), random.choice(_ALL_MODIFIERS))

        try:
            if moves[-1].basic_move == move.basic_move:
                continue
        except IndexError:  # The list is empty now
            pass

        try:
            if moves[-1].is_opposite(move):
                if moves[-2].basic_move == move.basic_move:
                    continue
        except IndexError:  # The list is empty or it has only one element
            pass

        moves.append(move)
        break
