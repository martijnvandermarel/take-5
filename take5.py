from abc import ABC
from random import shuffle

class CardTooLowException(Exception):
    pass

class Card(int):
    @property
    def points(self):
        if self == 55:
            return 7
        elif self in [11, 22, 33, 44, 66, 77, 88, 99]:
            return 5
        elif self in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
            return 3
        elif self in [5, 15, 25, 35, 45, 65, 75, 85, 95]:
            return 2
        else:
            return 1

class Row:
    CARD_LIMIT = 5

    def __init__(self) -> None:
        self.cards = []

    def __repr__(self) -> str:
        return " ".join([f"{c:3}" for c in self.cards])
    
    @property
    def length(self):
        return len(self.cards)
    
    @property
    def empty(self) -> bool:
        return self.length == 0
    
    @property
    def full(self) -> bool:
        return self.length >= self.CARD_LIMIT
    
    @property
    def head(self) -> Card:
        return self.cards[-1] if not self.empty else None
        
    @property
    def points(self) -> int:
        return sum([card.points for card in self.cards])
    
    def clear(self, new_card : Card = None) -> int:
        pts = self.points
        if new_card:
            self.cards = [new_card]
        else:
            self.cards = []
        return pts
    
    def add_card(self, card : Card) -> int:
        """
        Returns the number of points for the player if the row was full, otherwise zero
        """
        if not self.empty and card <= self.head:
            raise CardTooLowException()
        if self.full:
            pts = self.clear()
        else:
            pts = 0
        self.cards.append(card)
        return pts
        
class Board:
    NR_ROWS = 4

    def __init__(self) -> None:
        self.rows = [Row() for _ in range(self.NR_ROWS)]

    def __repr__(self) -> str:
        return "\n".join([str(r) for r in self.rows])
    
    def __iter__(self) -> Row:
        for row in self.rows:
            yield row

    def clear(self):
        for row in self.rows:
            row.clear()
    
    def play_card(self, card : Card) -> int:
        """
        Returns:
            -1 if card is lower than any rows -> player can choose which row to take
             p otherwise, p being the number of points for the player
        """
        # if any row is empty, card is played there
        for row in self.rows:
            if row.empty:
                return row.add_card(card)
        heads = [r.head for r in self.rows]
        # check if played card lower than any heads
        if not any([i < card for i in heads]):
            return -1
        # find highest head lower than played card
        head = max(i for i in heads if i < card)
        row_index = heads.index(head)
        return self.rows[row_index].add_card(card)

    def clear_row(self, row_index : int, new_card : Card) -> int:
        return self.rows[row_index].clear(new_card)

class Player(ABC):
    def __init__(self, id) -> None:
        self.id = id
        self.points = 0

    def receive_hand(self, hand : list[Card]):
        self.hand = hand

    def add_points(self, points : int):
        self.points += points

    def clear_points(self):
        self.points = 0

    def choose_card(self, board : Board) -> Card:
        """Returns a card"""
        raise NotImplementedError()
    
    def choose_row(self, board : Board) -> int:
        """Returns a row index"""
        raise NotImplementedError()

class Take5:
    NR_TURNS = 10
    NR_CARDS = 104
    def __init__(self, players : list[Player], quiet : bool = False) -> None:
        self.players = players
        self.num_players = len(players)
        if self.num_players > 10:
            raise ValueError("Too many players")
        self.board = Board()
        self.quiet = quiet

    def deal(self):
        self.board.clear()
        deck = [Card(i) for i in range(1, self.NR_CARDS + 1)]
        shuffle(deck)
        for player in self.players:
            deck, hand = deck[:-self.NR_TURNS], deck[-self.NR_TURNS:]
            player.receive_hand(hand)
        for row in self.board:
            row.add_card(deck.pop())

    def print(self, s):
        if not self.quiet:
            print(s)

    def round(self):
        self.print("\n\nNEW ROUND")
        self.deal()

        for i in range(self.NR_TURNS):
            self.print("\n-----------------")
            self.print(f"Turn {i + 1}")
            self.print("-----------------")
            self.print(self.board)
            played_cards = dict()
            for player in self.players:
                played_cards[player] = player.choose_card(self.board)
                card_players = {card : player for player, card in played_cards.items()}
            played_cards = list(played_cards.values())
            played_cards.sort()
            for card in played_cards:
                player = card_players[card]
                self.print(f"Player {player.id} plays {card}")
                points = self.board.play_card(card)
                if points == -1:
                    self.print(f"Player {player.id} has to choose a row to take")
                    row_index = player.choose_row(self.board)
                    self.print(f"Player {player.id} takes row {row_index + 1}")
                    points = self.board.clear_row(row_index, card)
                if points != 0:
                    self.print(f"Player {player.id} receives {points} points")
                player.add_points(points)
                self.print(self.board)
            self.print("-----------------")
        
        self.print("Round results:")
        for player in self.players:
            self.print(f"Player {player.id}: {player.points}")
        return {player.id: player.points for player in self.players}
