import sys
from enum import Enum, auto
from functools import reduce
from copy import deepcopy

from dataclasses import dataclass
import random


class MatchDirection(Enum):
    Horizontal = auto()
    Vertical = auto()


@dataclass(frozen=True)
class Match:
    direction: MatchDirection
    row: int
    col: int
    length: int


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


@dataclass(frozen=True)
class BoardState:
    board: Board
    score: int

    def process_cascade(self, symbols) -> 'BoardState':
        matches = self.find_matches(self.board)
        if not matches:
            return self

        # Вместо того, чтобы делать wrapper Pipe я решил переместить методы работы с доской в данный класс
        # Поскольку каждый из методов ниже возвращает объект BoardState, мы
        # можем легко композировать методы этого класса без дополнительного метода Pipe
        return (
            self
            .remove_matches(matches)
            .fill_empty_spaces(symbols)
            .process_cascade(symbols)
        )

    def find_matches(cls, board: Board) -> list[Match]:
        matches: list[Match] = []

        # Горизонтальные комбинации
        for row in range(board.size):
            start_col = 0
            for col in range(1, board.size):
                # Пропускаем ячейки в начале строки
                if board.cells[row][start_col].symbol == Element.EMPTY:
                    start_col = col
                    continue

                # Если текущая ячейка пустая, обрываем текущую последовательность
                if board.cells[row][col].symbol == Element.EMPTY:
                    cls.add_match_if_valid(
                        matches,
                        row,
                        start_col,
                        col - start_col,
                        MatchDirection.Horizontal,
                    )
                    start_col = col + 1
                    continue

                # Проверяем совпадение символов для непустых ячеек
                if board.cells[row][col].symbol != board.cells[row][start_col].symbol:
                    cls.add_match_if_valid(
                        matches,
                        row,
                        start_col,
                        col - start_col,
                        MatchDirection.Horizontal,
                    )
                    start_col = col
                elif col == board.size - 1:
                    cls.add_match_if_valid(
                        matches,
                        row,
                        start_col,
                        col - start_col + 1,
                        MatchDirection.Horizontal,
                    )

        # Вертикальные комбинации
        for col in range(board.size):
            start_row = 0
            for row in range(1, board.size):
                # Пропускаем ячейки в начале строки
                if board.cells[start_row][col].symbol == Element.EMPTY:
                    start_row = row
                    continue

                # Если текущая ячейка пустая, обрываем текущую последовательность
                if board.cells[row][col].symbol == Element.EMPTY:
                    cls.add_match_if_valid(
                        matches,
                        start_row,
                        col,
                        row - start_row,
                        MatchDirection.Vertical,
                    )
                    start_row = row + 1
                    continue

                # Проверяем совпадение символов для непустых ячеек
                if board.cells[row][col].symbol != board.cells[start_row][col].symbol:
                    cls.add_match_if_valid(
                        matches,
                        start_row,
                        col,
                        row - start_row,
                        MatchDirection.Vertical,
                    )
                    start_row = row
                elif row == board.size - 1:
                    cls.add_match_if_valid(
                        matches,
                        start_row,
                        col,
                        row - start_row + 1,
                        MatchDirection.Vertical,
                    )

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
        removed_count: int = reduce(lambda x, y: x + y.length, matches)
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


class Game:
    SYMBOLS = ["A", "B", "C", "D", "E", "F"]

    @staticmethod
    def draw(board: Board):
        print("   0 1 2 3 4 5 6 7")
        for i in range(8):
            print(i, " ", end="")
            for j in range(8):
                print(board.cells[i][j].symbol, end=" ")
            print()
        print()

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
            .fill_empty_spaces(cls.SYMBOLS)
            .process_cascade(cls.SYMBOLS)
        )


def main():
    bs: BoardState = Game.initialize_game()
    while True:
        Game.draw(bs.board)
        bs = Game.read_move(bs)


if __name__ == "__main__":
    main()
