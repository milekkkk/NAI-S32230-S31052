"""
Zasady gry: https://en.wikipedia.org/wiki/Hex_(board_game)
Autorzy: Miłosz Kurszewski s32230 i Łukasz Burnicki s31052
Przygotowanie środowiska: zobacz README.md; uruchom main.py interpreterem .venv.
Sztuczna inteligencja: easyAI Negamax z alfa-beta, przeszukujący 3 półruchy.
X łączy górny i dolny brzeg planszy. O łączy lewy i prawy brzeg.
"""

from collections import deque

from easyAI import AI_Player, Human_Player, Negamax, TwoPlayerGame


BOARD_SIZE = 5
EMPTY = 0
PLAYER_X = 1
PLAYER_O = 2
COLUMNS = "ABCDE"


class HexGame(TwoPlayerGame):
    """Reprezentuje stan gry Hex na planszy 5 na 5."""

    def __init__(self, players):
        """Utwórz pustą planszę i ustaw gracza X jako rozpoczynającego.

        Parameters:
            players (list): Gracz człowiek i gracz sterowany przez AI.
        """
        self.players = players
        self.current_player = PLAYER_X
        self.board = [
            [EMPTY for _ in range(BOARD_SIZE)]
            for _ in range(BOARD_SIZE)
        ]

    def possible_moves(self):
        """Zwróć współrzędne wszystkich pól, na których można wykonać ruch.

        Returns:
            list[str]: Wolne pola zapisane jako współrzędne, np. A1.
        """
        moves = []

        for row in range(BOARD_SIZE):
            for column in range(BOARD_SIZE):
                if self.board[row][column] == EMPTY:
                    moves.append(f"{COLUMNS[column]}{row + 1}")

        return moves

    def make_move(self, move):
        """Postaw znak bieżącego gracza na wolnym polu wskazanym przez easyAI.

        Parameters:
            move (str): Współrzędne wolnego pola, na przykład A1.
        """
        column = COLUMNS.index(move[0])
        row = int(move[1]) - 1
        self.board[row][column] = self.current_player

    def is_over(self):
        """Sprawdź, czy któryś gracz połączył swoje przeciwległe brzegi.

        Returns:
            bool: True, gdy gra się skończyła; w przeciwnym razie False.
        """
        return self.winner() is not None

    def winner(self):
        """Ustal zwycięzcę aktualnej partii.

        Returns:
            int | None: Numer zwycięskiego gracza albo None, gdy gra trwa.
        """
        if self.has_connection(PLAYER_X):
            return PLAYER_X
        if self.has_connection(PLAYER_O):
            return PLAYER_O
        return None

    def has_connection(self, player):
        """Sprawdź, czy gracz połączył swoje dwa brzegi planszy.

        X łączy górny i dolny brzeg, a O lewy i prawy.

        Parameters:
            player (int): Numer gracza, którego połączenie sprawdzamy.

        Returns:
            bool: True, jeśli gracz ma połączenie między brzegami.
        """
        if player == PLAYER_X:
            starts = [(0, column) for column in range(BOARD_SIZE)]
        else:
            starts = [(row, 0) for row in range(BOARD_SIZE)]

        queue = deque()
        visited = set()

        for cell in starts:
            row, column = cell
            if self.board[row][column] == player:
                queue.append(cell)
                visited.add(cell)

        while queue:
            row, column = queue.popleft()

            if player == PLAYER_X and row == BOARD_SIZE - 1:
                return True
            if player == PLAYER_O and column == BOARD_SIZE - 1:
                return True

            for next_row, next_column in self.neighbors(row, column):
                neighbor = (next_row, next_column)

                if (
                    self.board[next_row][next_column] == player
                    and neighbor not in visited
                ):
                    visited.add(neighbor)
                    queue.append(neighbor)

        return False

    def neighbors(self, row, column):
        """Wygeneruj pola sąsiadujące z podanym polem w planszy Hex.

        Parameters:
            row (int): Indeks wiersza pola.
            column (int): Indeks kolumny pola.

        Yields:
            tuple[int, int]: Indeksy wiersza i kolumny sąsiada.
        """
        directions = [
            (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
                      (1, -1), (1, 0),
        ]

        for row_change, column_change in directions:
            next_row = row + row_change
            next_column = column + column_change

            if (
                0 <= next_row < BOARD_SIZE
                and 0 <= next_column < BOARD_SIZE
            ):
                yield next_row, next_column

    def scoring(self):
        """Oceń pozycję z perspektywy gracza, który ma teraz ruch.

        Returns:
            int: Wynik pozycji dla algorytmu Negamax.
        """
        winner = self.winner()

        if winner is not None:
            if winner == self.current_player:
                return 1000
            return -1000

        center = BOARD_SIZE // 2
        score = 0

        for row in range(BOARD_SIZE):
            for column in range(BOARD_SIZE):
                owner = self.board[row][column]
                value = BOARD_SIZE - abs(row - center) - abs(column - center)

                if owner == self.current_player:
                    score += value
                elif owner != EMPTY:
                    score -= value

        return score

    def show(self):
        """Wyswietl aktualna planszę z wcięciami pokazujacymi jej uklad."""
        print("\nCel X (człowiek): góra ↕ dół")
        print("Cel O (komputer): lewo ↔ prawo")
        print("     " + "   ".join(COLUMNS))

        for row in range(BOARD_SIZE):
            cells = []

            for column in range(BOARD_SIZE):
                owner = self.board[row][column]

                if owner == PLAYER_X:
                    symbol = "X"
                elif owner == PLAYER_O:
                    symbol = "O"
                else:
                    symbol = "."

                cells.append(f" {symbol} ")

            indentation = " " * (row * 2)
            print(f"{row + 1:>2}  {indentation}" + " ".join(cells))


def play_game(game):
    """Prowadz partie i wypisuj, kto wykonal kazdy ruch.

    Parameters:
        game (HexGame): Partia do rozegrania.
    """
    move_number = 1
    game.show()

    while not game.is_over():
        player = game.current_player
        move = game.get_move()

        if player == PLAYER_X:
            print(f"\nRuch {move_number}: człowiek (X) wybiera {move}.")
        else:
            print(f"\nRuch {move_number}: AI (O) wybiera {move}.")

        game.make_move(move)
        game.switch_player()
        game.show()
        move_number += 1

    winner = game.winner()

    if winner == PLAYER_X:
        print("\nZwycięstwo Gracza!")
    elif winner == PLAYER_O:
        print("\nZwycięstwo AI!")


def main():
    """Utwórz graczy i rozpocznij partię człowieka z komputerem."""
    print("HEX — człowiek gra X, komputer gra O.")
    print("Wpisuj współrzędne wolnego pola, na przykład A1 albo C4.")

    ai = Negamax(3, win_score=1000)
    players = [Human_Player(), AI_Player(ai)]
    game = HexGame(players)

    try:
        play_game(game)
    except KeyboardInterrupt:
        print("\nGra zakończona.")


if __name__ == "__main__":
    main()