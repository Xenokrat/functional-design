import sys
import random

from enum import StrEnum
from dataclasses import dataclass


class Element(StrEnum):
    EMPTY = '0'
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    E = 'E'
    F = 'F'


@dataclass
class Board:
    size: int
    cells: list[list[Element]] = None

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
        size=8,
        cells=[
            [random.choice(list(Element)[1:]) for _ in range(8)]
            for _ in range(8)
        ],
    )
    return BoardState(board=board, score=0)


if __name__ == "__main__":
    board_state = initialize_game()
    while True:
        draw(board_state.board)
        board_state = read_move(board_state)
