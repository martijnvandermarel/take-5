from abc import ABC
from random import shuffle, choice, randrange
from math import exp

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

class ManualPlayer(Player):
    def choose_card(self, board : Board) -> Card:
        print(f"Player '{self.id}' has to choose a card to play")
        print(f"Hand: {sorted(self.hand)}")
        card = None
        while card not in self.hand:
            card_input = input("Card to play: ")
            try:
                card = Card(card_input)
            except:
                continue
        self.hand.remove(card)
        return card
    
    def choose_row(self, board : Board) -> int:
        """Returns a row index"""
        print(f"Player '{self.id}' has to choose a row to receive")
        print(f"Points per row: {[row.points for row in board]}")
        row = None
        while row not in [1, 2, 3, 4]:
            row_input = input("Row index to pick (1, 2, 3, 4): ")
            try:
                row = int(row_input)
            except:
                continue
        return row - 1
    
class MinimumRowPointPlayer(Player):
    def choose_row(self, board : Board) -> int:
        """Choose the row with lowest number of points"""
        row_points = [row.points for row in board]
        return row_points.index(min(row_points))
    
class RandomPlayer(MinimumRowPointPlayer):
    def choose_card(self, board : Board) -> Card:
        """Pick a random card"""
        card = self.hand.pop(randrange(len(self.hand)))
        return card
    
class AscendingPlayer(MinimumRowPointPlayer):
    def choose_card(self, board : Board) -> Card:
        """Pick the lowest card available"""
        self.hand.sort(reverse=True)
        card = self.hand.pop()
        return card
    
class DescendingPlayer(MinimumRowPointPlayer):
    def choose_card(self, board : Board) -> Card:
        """Pick the highest card available"""
        self.hand.sort()
        card = self.hand.pop()
        return card
    
class SmallestGapPlayer(MinimumRowPointPlayer):
    def choose_card(self, board : Board) -> Card:
        """Pick the card with the smallest gap to a not-full row head"""
        heads = [row.head for row in board if not row.full]
        best_card_so_far = self.hand[0]
        smallest_gap_so_far = 1000
        for card in self.hand:
            # try to avoid picking card lower than any heads
            if not any([head < card for head in heads]):
                continue
            # find highest head lower than played card
            head = max([i for i in heads if i < card])
            gap  = card - head
            if gap < smallest_gap_so_far:
                best_card_so_far = card
                smallest_gap_so_far = gap
        self.hand.remove(best_card_so_far)
        return best_card_so_far

class ShortestRowPlayer(MinimumRowPointPlayer):
    def choose_card(self, board : Board) -> Card:
        """Pick the lowest card for the shortest row, with gap as tiebreaker"""
        heads = [row.head for row in board]
        lengths = [row.length for row in board]
        best_card_so_far = self.hand[0]
        shortest_length_so_far = 6
        best_card_gap_so_far = 105
        for card in self.hand:
            # try to avoid picking card lower than any heads
            if not any([head < card for head in heads]):
                continue
            # find highest head lower than played card
            head = max([i for i in heads if i < card])
            index = heads.index(head)
            length = lengths[index]
            gap  = card - head
            if length < shortest_length_so_far or (length == shortest_length_so_far and gap < best_card_gap_so_far):
                best_card_so_far = card
                shortest_length_so_far = length
                best_card_gap_so_far = gap
        self.hand.remove(best_card_so_far)
        return best_card_so_far
    
class CostFunPlayer(MinimumRowPointPlayer):
    def __init__(self, id, num_players : int, alpha : float = 0.3) -> None:
        super().__init__(id)
        self.num_players = num_players
        self.alpha = alpha

    def choose_card(self, board: Board) -> Card:
        heads = [row.head for row in board]
        lengths = [row.length for row in board]
        points = [row.points for row in board]

        def cost_fun(card : Card) -> float:
            if not any([head < card for head in heads]):
                # have to take a row, assuming min points row
                #TODO: differentiate within these cards
                cost = min(points)
                return cost
            head = max([i for i in heads if i < card])
            index = heads.index(head)
            length = lengths[index]
            gap  = card - head
            pts = points[index]
            limit = board.rows[index].CARD_LIMIT
            cards_before_limit = limit - length
            if cards_before_limit == 0:
                est_chance_of_taking = 1.0
            elif self.num_players <= cards_before_limit or gap == 1:
                est_chance_of_taking = 0.0
            else:
                space_chance = 1.0 - cards_before_limit / self.num_players
                gap_chance = 1 - exp(-self.alpha * (gap - 1))
                est_chance_of_taking = space_chance * gap_chance
            cost = pts * est_chance_of_taking
            return cost
        
        best_value_so_far = 0.0
        best_card_so_far = None
        for card in self.hand:
            value = 1 / (cost_fun(card) + 0.001)
            if value > best_value_so_far:
                best_value_so_far = value
                best_card_so_far = card
        self.hand.remove(best_card_so_far)
        return best_card_so_far


class CheatingBastard(Player):
    """This strategy is very good at avoiding any penalty points """

    def choose_card(self, board: Board) -> Card:
        return Card(1)

    def choose_row(self, board: Board) -> int:
        """Oops"""
        board.rows[0].clear()
        return 0


class Take5:
    NR_TURNS = 10
    NR_CARDS = 104
    def __init__(self, players : list[Player], quiet : bool = False) -> None:
        self.players = players
        self.num_players = len(players)
        if self.num_players > 10:
            raise ValueError("Too many players")
        self.board = Board()
        if any([isinstance(player, ManualPlayer) for player in players]) and quiet:
            raise ValueError("Can't play in quiet mode if manual players are playing")
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

if __name__ == "__main__":
    NR_ROUNDS = 10000
    # players = [RandomPlayer(i+1) for i in range(4)]
    players = [
        # ManualPlayer('Jitske'),
        # ManualPlayer('Martijn'),
        # RandomPlayer('randbot 1'),
        # RandomPlayer('randbot 2'),
        # RandomPlayer('randbot 3'),
        CostFunPlayer('martijnbot 1', num_players=4, alpha=0.3),
        ShortestRowPlayer('martijnbot 2'),
        DescendingPlayer('martijnbot 3'),
        SmallestGapPlayer('martijnbot 4'),
        CheatingBastard('Isha'),
    ]
    take5 = Take5(players, quiet=True)
    stats = dict()
    for round in range(NR_ROUNDS):
        round_stats = take5.round()
        stats = {p.id: stats.get(p.id, 0) + round_stats.get(p.id, 0) for p in players}
        for player in players:
            player.clear_points()

    print(f"Point totals after {NR_ROUNDS} rounds:")
    for player in players:
        pts = stats.get(player.id, 0)
        print(f"Player {player.id}: {pts} ({pts / NR_ROUNDS} per round)")