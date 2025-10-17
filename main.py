import sys

from dataclasses import dataclass
import random


@dataclass(frozen=True)
class Element:
    symbol: str
    EMPTY: str = '0'


@dataclass
class Board:
    size: int
    cells: list[list[Element]] = None

    # Cringe
    def __post_init__(self):
        if not self.cells:
            self.cells = \
                [[Element(Element.EMPTY) for _ in range(self.size)] for _ in range(self.size)]


@dataclass(frozen=True)
class BoardState:
    board: Board
    score: int


class Game:
    SYMBOLS = ['A', 'B', 'C', 'D', 'E', 'F']

    @staticmethod
    def draw(board: Board):
        print("   0 1 2 3 4 5 6 7")
        for i in range(8):
            print(i, " ", end='')
            for j in range(8):
                print(board.cells[i][j].symbol, end=' ')
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
        inp = input('> ')
        if inp == 'q':
            sys.exit(0)

        board = Game.clone_board(board_state.board)
        coords: list[str] = inp.split(' ')
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
            cells=[[Element(random.choice(cls.SYMBOLS)) for _ in range(8)] for _ in range(8)]
        )
        return BoardState(board=board, score=0)


def main():
    bs: BoardState = Game.initialize_game()
    while True:
        Game.draw(bs.board)
        bs = Game.read_move(bs)


if __name__ == "__main__":
    main()
