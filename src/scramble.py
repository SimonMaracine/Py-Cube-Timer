from __future__ import annotations

import enum
import dataclasses
import random
from typing import List


class BasicMove(enum.Enum):
    R = "R"
    L = "L"
    U = "U"
    D = "D"
    F = "F"
    B = "B"


class Modifier(enum.Enum):
    NONE = ""
    PRIME = "'"
    TWO = "2"


@dataclasses.dataclass
class Move:
    basic_move: BasicMove
    modifier: Modifier

    def combined(self) -> str:
        return self.basic_move.value + self.modifier.value

    def is_opposite(self, other: Move) -> bool:
        if self.basic_move == BasicMove.R:
            return other.basic_move == BasicMove.L
        elif self.basic_move == BasicMove.L:
            return other.basic_move == BasicMove.R
        elif self.basic_move == BasicMove.U:
            return other.basic_move == BasicMove.D
        elif self.basic_move == BasicMove.D:
            return other.basic_move == BasicMove.U
        elif self.basic_move == BasicMove.F:
            return other.basic_move == BasicMove.B
        elif self.basic_move == BasicMove.B:
            return other.basic_move == BasicMove.F


ALL_BASIC_MOVES = (BasicMove.R, BasicMove.L, BasicMove.U, BasicMove.D, BasicMove.F, BasicMove.B)
ALL_MODIFIERS = (Modifier.NONE, Modifier.PRIME, Modifier.TWO)


def generate_scramble() -> str:
    moves: List[Move] = []

    while len(moves) < 20:
        _append_move(moves)

    final = [move.combined() for move in moves]
    return " ".join(final)


def _append_move(moves: List[Move]):
    while True:
        move = Move(random.choice(ALL_BASIC_MOVES), random.choice(ALL_MODIFIERS))

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
