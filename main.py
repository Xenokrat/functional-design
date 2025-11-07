import sys
import random
from copy import deepcopy
from functools import reduce

from enum import StrEnum, Enum, auto
from dataclasses import dataclass


class Element(StrEnum):
    EMPTY = "0"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"


class MatchDirection(Enum):
    HORIZONTAL = auto()
    VERTICAL = auto()


@dataclass
class Match:
    direction: MatchDirection
    row: int
    col: int
    length: int


@dataclass
class Board:
    size: int
    cells: list[list[Element]] = []

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


def draw(board: Board, msg: str | None = None):
    if msg:
        print(msg)
    print("   0 1 2 3 4 5 6 7")
    for i in range(8):
        print(i, " ", end="")
        for j in range(8):
            print(board.cells[i][j].value, end=" ")
        print()
    print()


def clone_board(board: Board) -> Board:
    new_board = Board(board.size)
    for i in range(board.size):
        for j in range(board.size):
            new_board.cells[i][j] = board.cells[i][j]
    return new_board


def read_move(board_state: BoardState) -> BoardState:
    inp = input(">")
    if inp == "q":
        sys.exit(0)

    board = clone_board(board_state.board)
    coords: list[str] = inp.split(" ")
    x = int(coords[1])
    y = int(coords[0])
    x1 = int(coords[3])
    y1 = int(coords[2])
    e: Element = board.cells[x][y]
    board.cells[x][y] = board.cells[x1][y1]
    board.cells[x1][y1] = e
    return BoardState(board=board, score=board_state.score)


def initialize_game(board_size: int = 8) -> BoardState:
    # 1. Создать новую "Доску"
    # 2. Заполнить доску случайными элементами
    # 3. Создать новый объект BoardState,
    #    содержащий созданную доску из п.2 со значением score = 0
    # 4. Вернуть объект BoardState
    board = Board(
        size=board_size,
        cells=[
            [random.choice(list(Element)[1:]) for _ in range(board_size)]
            for _ in range(board_size)
        ],
    )
    return BoardState(board=board, score=0)



def find_matches(board: Board) -> list[Match]:
    matches: list[Match] = []

    # Горизонтальные комбинации
    for row in range(board.size):
        start_col = 0
        for col in range(1, board.size):
            # Пропускаем ячейки в начале строки
            if board.cells[row][start_col] == Element.EMPTY:
                start_col = col
                continue

            # Если текущая ячейка пустая, обрываем текущую последовательность
            if board.cells[row][col] == Element.EMPTY:
                add_match_if_valid(
                    matches,
                    row,
                    start_col,
                    col - start_col,
                    MatchDirection.HORIZONTAL,
                )
                start_col = col + 1
                continue

            # Проверяем совпадение символов для непустых ячеек
            if board.cells[row][col] != board.cells[row][start_col]:
                add_match_if_valid(
                    matches,
                    row,
                    start_col,
                    col - start_col,
                    MatchDirection.HORIZONTAL,
                )
                start_col = col
            elif col == board.size - 1:
                add_match_if_valid(
                    matches,
                    row,
                    start_col,
                    col - start_col + 1,
                    MatchDirection.HORIZONTAL,
                )

    # Вертикальные комбинации
    for col in range(board.size):
        start_row = 0
        for row in range(1, board.size):
            # Пропускаем ячейки в начале строки
            if board.cells[start_row][col] == Element.EMPTY:
                start_row = row
                continue

            # Если текущая ячейка пустая, обрываем текущую последовательность
            if board.cells[row][col] == Element.EMPTY:
                add_match_if_valid(
                    matches,
                    start_row,
                    col,
                    row - start_row,
                    MatchDirection.VERTICAL,
                )
                start_row = row + 1
                continue

            # Проверяем совпадение символов для непустых ячеек
            if board.cells[row][col] != board.cells[start_row][col]:
                add_match_if_valid(
                    matches,
                    start_row,
                    col,
                    row - start_row,
                    MatchDirection.VERTICAL,
                )
                start_row = row
            elif row == board.size - 1:
                add_match_if_valid(
                    matches,
                    start_row,
                    col,
                    row - start_row + 1,
                    MatchDirection.VERTICAL,
                )

    return matches


def add_match_if_valid(
    matches: list[Match],
    row: int, col: int, length: int,
    direction: MatchDirection
):
    if length >= 3:
        matches.append(Match(direction, row, col, length))


def remove_matches(board_state: BoardState, matches: list[Match]) -> BoardState:
    if not matches:
        return board_state

    # 1. Mark cells to delete
    marked_cells: list[list[Element]] = mark_cells_for_removal(
        board_state.board, matches
    )

    # 2. Apply graviation
    gravity_applied_cells = apply_gravity(marked_cells, board_state.board.size)

    # 3. Update score
    removed_count: int = reduce(lambda x, y: x + y.length, matches, 0)
    new_score: int = board_state.score + calculate_score(removed_count)

    return BoardState(
        board=Board(size=board_state.board.size, cells=gravity_applied_cells),
        score=new_score,
    )


def mark_cells_for_removal(board: Board, matches: list[Match]) -> list[list[Element]]:
    new_cells = deepcopy(board.cells)

    for match in matches:
        for i in range(match.length):
            row = (
                match.row
                if match.direction == MatchDirection.HORIZONTAL
                else match.row + i
            )
            col = (
                match.col
                if match.direction == MatchDirection.VERTICAL
                else match.col + i
            )
            new_cells[row][col] = Element(Element.EMPTY)

    return new_cells


def apply_gravity(cells: list[list[Element]], size: int) -> list[list[Element]]:
    new_cells = [[Element(Element.EMPTY) for _ in range(size)] for _ in range(size)]

    for col in range(size):
        new_row = size - 1
        for row in range(size - 1, -1, -1):
            if cells[row][col] != Element.EMPTY:
                new_cells[new_row][col] = cells[row][col]
                new_row -= 1

    return new_cells


def calculate_score(removed_count: int) -> int:
    return removed_count * 10


def fill_empty_spaces(board_state: BoardState) -> BoardState:
    if not board_state.board.cells:
        return board_state

    new_cells: list[list[Element]] = deepcopy(board_state.board.cells)

    for row in range(board_state.board.size):
        for col in range(board_state.board.size):
            if new_cells[row][col] == Element.EMPTY:
                new_cells[row][col] = random.choice(list(Element)[1:])

    return BoardState(
        board=Board(size=board_state.board.size, cells=new_cells),
        score=board_state.score,
    )


def process_cascade(board_state: BoardState) -> BoardState:
    matches = find_matches(board_state.board)
    if not matches:
        return board_state

    new_state1 = remove_matches(board_state, matches)
    new_state2 = fill_empty_spaces(new_state1)
    return process_cascade(new_state2)


if __name__ == "__main__":
    board_state = initialize_game()
    while True:
        draw(board_state.board)
        board_state = read_move(board_state)
