from math import exp
from random import randrange

from take5 import Player, Card, Board

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
    # TODO: it can be more optimal to not choose the minimum row always
    # For example if you can force more points on another player
    def choose_row(self, board : Board) -> int:
        """Choose the row with lowest number of points"""
        row_points = [row.points for row in board]
        return row_points.index(min(row_points))
    
class RandomPlayer(MinimumRowPointPlayer):
    def choose_card(self, board : Board) -> Card:
        """Pick a random card"""
        return self.hand[randrange(len(self.hand))]
    
class AscendingPlayer(MinimumRowPointPlayer):
    def choose_card(self, board : Board) -> Card:
        """Pick the lowest card available"""
        self.hand.sort()
        return self.hand[0]

class DescendingPlayer(MinimumRowPointPlayer):
    def choose_card(self, board : Board) -> Card:
        """Pick the highest card available"""
        self.hand.sort()
        return self.hand[-1]
    
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
        return best_card_so_far
