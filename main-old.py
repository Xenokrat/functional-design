from re import Pattern
from pathlib import Path
import sys
from enum import Enum, auto
from functools import reduce
from copy import deepcopy

from dataclasses import dataclass
import random


DEBUG = True


class MatchDirection(Enum):
    Horizontal = auto()
    Vertical = auto()


# @dataclass(frozen=True)
# class Match:
#     direction: MatchDirection
#     row: int
#     col: int
#     length: int


@dataclass(frozen=True)
class Element:
    symbol: str
    EMPTY: str = "0"


@dataclass
class Board:
    size: int
    cells: list[list[Element]] = None

    # Cringe
    def __post_init__(self):
        if not self.cells:
            self.cells = [
                [Element(Element.EMPTY) for _ in range(self.size)]
                for _ in range(self.size)
            ]


@dataclass
class Position:
    row: int
    col: int


@dataclass
class Match:
    name: str
    origin: Position
    width: int
    height: int
    pattern: list[Position]

    def __post_init__(self):
        for pos in self.pattern:
            if pos.row < 0 or pos.row >= self.height or pos.col < 0 or pos.col >= self.width:
                raise ValueError("Relative position outside bounds")

    def get_absolute_positions(self) -> list[Position]:
        origin_row = self.origin.row
        origin_col = self.origin.col
        return [Position(rp.row + origin_row, rp.col + origin_col) for rp in self.pattern]


def generate_level_matches() -> list[Match]:
    horizontal_match = Match(
        name="Горизонтальная комбинация три-в-ряд",
        origin=Position(0, 0),
        width=3,
        height=1,
        pattern=[
            Position(0, 0),
            Position(0, 1),
            Position(0, 2),
        ]
    )
    vertical_match = Match(
        name="Вертикальная комбинация три-в-ряд",
        origin=Position(0, 0),
        width=1,
        height=3,
        pattern=[
            Position(0, 0),
            Position(1, 0),
            Position(2, 0),
        ]
    )
    return [horizontal_match, vertical_match]



@dataclass(frozen=True)
class BoardState:
    board: Board
    score: int

    def draw(self, msg: str | None = None, debug_mode: bool = False) -> 'BoardState':
        if not debug_mode:
            return self

        if msg:
            print(msg)
        board = self.board
        print("   0 1 2 3 4 5 6 7")
        for i in range(8):
            print(i, " ", end="")
            for j in range(8):
                print(board.cells[i][j].symbol, end=" ")
            print()
        print()
        return self

    def process_cascade(self, symbols) -> 'BoardState':
        matches = self.find_matches(self.board)
        if not matches:
            return self

        # Вместо того, чтобы делать wrapper Pipe я решил переместить методы работы с доской в данный класс
        # Поскольку каждый из методов ниже возвращает объект BoardState, мы
        # можем легко композировать методы этого класса без дополнительного метода Pipe
        return (
            self
            .draw("Init Board", debug_mode = DEBUG)
            .remove_matches(matches)
            .draw("Remove Matches", debug_mode = DEBUG)
            .fill_empty_spaces(symbols)
            .draw("Fill Empty Spaces", debug_mode = DEBUG)
            .process_cascade(symbols)
            .draw("Result", debug_mode = DEBUG)
        )


def find_matches(bs: BoardState, patterns: list[Match]) -> list[Match]:
    matches: list[Match] = []
    board = bs.board

    for pattern in patterns:
        if len(pattern.pattern) == 0:
            continue

        for row in range(board.size - pattern.height + 1):
            for col in range(board.size - pattern.width + 1):
                candidate_origin = Position(row, col)
                first_element = board.cells[row][col]

                if first_element == Element.EMPTY:
                    continue

                is_valid = True

                for rel_pos in pattern.pattern:
                    abs_row = row + rel_pos.row
                    abs_col = col + rel_pos.col

                    if board.cells[abs_row][abs_col] == Element.EMPTY \
                        or not board.cells[abs_row][abs_col] == first_element:
                        is_valid = False
                        break

                if is_valid:
                    matches.append(Match(
                       pattern.name,
                       candidate_origin,
                       pattern.width,
                       pattern.height,
                       pattern.pattern,
                   ))
    return matches





    @staticmethod
    def add_match_if_valid(
        matches: list[Match], row: int, col: int, length: int, direction: MatchDirection
    ):
        if length >= 3:
            matches.append(Match(direction, row, col, length))

    def remove_matches(
        self, matches: list[Match]
    ) -> 'BoardState':
        if not matches:
            return self

        # 1. Mark cells to delete
        marked_cells: list[list[Element]] = self.mark_cells_for_removal(
            self.board, matches
        )

        # 2. Apply graviation
        gravity_applied_cells = self.apply_gravity(
            marked_cells, self.board.size
        )

        # 3. Update score
        removed_count: int = reduce(lambda x, y: x + y.length, matches, 0)
        new_score: int = self.score + self.calculate_score(removed_count)

        return BoardState(
            board=Board(size=self.board.size, cells=gravity_applied_cells),
            score=new_score,
        )

    @staticmethod
    def mark_cells_for_removal(
        board: Board, matches: list[Match]
    ) -> list[list[Element]]:
        new_cells = deepcopy(board.cells)

        for match in matches:
            for i in range(match.length):
                row = (
                    match.row
                    if match.direction == MatchDirection.Horizontal
                    else match.row + i
                )
                col = (
                    match.col
                    if match.direction == MatchDirection.Vertical
                    else match.col + i
                )
                new_cells[row][col] = Element(Element.EMPTY)

        return new_cells

    @staticmethod
    def apply_gravity(cells: list[list[Element]], size: int) -> list[list[Element]]:
        new_cells = [[Element(Element.EMPTY) for _ in range(size)] for _ in range(size)]

        for col in range(size):
            new_row = size - 1
            for row in range(size - 1, -1, -1):
                if cells[row][col].symbol != Element.EMPTY:
                    new_cells[new_row][col] = cells[row][col]
                    new_row -= 1

        return new_cells

    @staticmethod
    def calculate_score(removed_count: int) -> int:
        return removed_count * 10

    def fill_empty_spaces(self, symbols) -> 'BoardState':
        if not self.board.cells:
            return self

        new_cells: list[list[Element]] = deepcopy(self.board.cells)

        for row in range(self.board.size):
            for col in range(self.board.size):
                if new_cells[row][col].symbol == Element.EMPTY:
                    new_cells[row][col] = Element(random.choice(symbols))

        return BoardState(
            board=Board(size=self.board.size, cells=new_cells),
            score=self.score,
        )


def process_cascade(board_state: BoardState, symbols: list[str], debug_mode = False) -> BoardState:
    matches = board_state.find_matches(board_state.board)
    if not matches:
        return board_state

    return (
        board_state
        .draw("Init Board", debug_mode = DEBUG)
        .remove_matches(matches)
        .draw("Remove Matches", debug_mode = DEBUG)
        .fill_empty_spaces(symbols)
        .draw("Fill Empty Spaces", debug_mode = DEBUG)
        .process_cascade(symbols)
        .draw("Result", debug_mode = DEBUG)
    )

class Game:
    SYMBOLS = ["A", "B", "C", "D", "E", "F"]

    @staticmethod
    def draw(board_state: BoardState):
        board_state.draw()

    @staticmethod
    def clone_board(board: Board) -> Board:
        b = Board(board.size)
        for i in range(board.size):
            for j in range(board.size):
                b.cells[i][j] = board.cells[i][j]
        return b

    @staticmethod
    def read_move(board_state: BoardState):
        inp = input("> ")
        if inp == "q":
            sys.exit(0)

        board = Game.clone_board(board_state.board)
        coords: list[str] = inp.split(" ")
        x = int(coords[1])
        y = int(coords[0])
        x1 = int(coords[3])
        y1 = int(coords[2])
        e: Element = board.cells[x][y]
        board.cells[x][y] = board.cells[x1][y1]
        board.cells[x1][y1] = e

        return BoardState(board, board_state.score)

    @classmethod
    def initialize_game(cls, board_size: int = 8) -> BoardState:
        board = Board(
            size=8,
            cells=[
                [Element(random.choice(cls.SYMBOLS)) for _ in range(8)]
                for _ in range(8)
            ],
        )
        return (
            BoardState(board=board, score=0)
            .process_cascade(cls.SYMBOLS)
        )


def main():
    bs: BoardState = Game.initialize_game()
    while True:
        Game.draw(bs)
        bs = Game.read_move(bs)


if __name__ == "__main__":
    main()
