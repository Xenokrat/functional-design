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
    def initialize_game(cls) -> BoardState:
        # 1. Создать новую "Доску"
        # 2. Заполнить доску случайными элементами из класса Game
        # 3. Создать новый объект BoardState,
        #     содержащий созданную доску из п.2 со значением score = 0
        # 4. Вернуть объект BoardState
        board = Board(
            size=8,
            cells=[
                [Element(random.choice(cls.SYMBOLS)) for _ in range(8)]
                for _ in range(8)
            ],
        )
        return BoardState(board=board, score=0)

    @classmethod
    def process_cascade(cls, board_state: BoardState) -> BoardState:
        matches = cls.find_matches(board_state.board)
        if not matches:
            return board_state

        new_state1 = cls.remove_matches(board_state, matches)
        new_state2 = cls.fill_empty_spaces(new_state1)
        return cls.process_cascade(new_state2)


    @classmethod
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

    @classmethod
    def remove_matches(
        cls, current_state: BoardState, matches: list[Match]
    ) -> BoardState:
        if not matches:
            return current_state

        # 1. Mark cells to delete
        marked_cells: list[list[Element]] = cls.mark_cells_for_removal(
            current_state.board, matches
        )

        # 2. Apply graviation
        gravity_applied_cells = cls.apply_gravity(
            marked_cells, current_state.board.size
        )

        # 3. Update score
        removed_count: int = reduce(lambda x, y: x + y.length, matches)
        new_score: int = current_state.score + cls.calculate_score(removed_count)

        return BoardState(
            board=Board(size=current_state.board.size, cells=gravity_applied_cells),
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

    @classmethod
    def fill_empty_spaces(cls, current_state: BoardState) -> BoardState:
        if not current_state.board.cells:
            return current_state

        new_cells: list[list[Element]] = deepcopy(current_state.board.cells)

        for row in range(current_state.board.size):
            for col in range(current_state.board.size):
                if new_cells[row][col].symbol == Element.EMPTY:
                    new_cells[row][col] = Element(random.choice(cls.SYMBOLS))

        return BoardState(
            board=Board(size=current_state.board.size, cells=new_cells),
            score=current_state.score,
        )


def main():
    bs: BoardState = Game.initialize_game()
    while True:
        Game.draw(bs.board)
        bs = Game.read_move(bs)


if __name__ == "__main__":
    main()
