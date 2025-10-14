from random import shuffle

import gymnasium as gym

import numpy as np

from take5 import Card, Player, Board, Row
from players import MinimumRowPointPlayer


class Take5Env(gym.Env):
    NR_TURNS = 10
    NR_CARDS = 104
    def __init__(self, config):
        self._opponents : list[Player] = config.get("opponents")
        if len(self._opponents) < 1:
            raise ValueError("At least one opponent must be provided")
        self._board = Board()
        self._played_cards = []
        # Though an agent is technically not part of the environment,
        # here it's used only as a convenient way to manage the agent's hand,
        # which are part of the environment.
        # Also the choose_row method is used.
        self._agent = MinimumRowPointPlayer("agent")
        
        self.observation_space = gym.spaces.Dict(
            {
                # Player's cards in hand (one-hot encoded)
                "hand": gym.spaces.MultiBinary(self.NR_CARDS),
                # Played cards (one-hot encoded)
                "played_cards": gym.spaces.MultiBinary(self.NR_CARDS),
                # Row lengths
                "row_lengths": gym.spaces.MultiDiscrete([Row.CARD_LIMIT + 1] * Board.NR_ROWS),
                # Row points (a row contains at most 27 points)
                "row_points": gym.spaces.MultiDiscrete([27 + 1] * Board.NR_ROWS),
                # Row heads
                "row_heads": gym.spaces.MultiDiscrete([self.NR_CARDS + 1] * Board.NR_ROWS),
            }
        )
        # Vector of ratings for each card in the deck
        # self.action_space = gym.spaces.Box(low=0, high=1, shape=(self.NR_CARDS,), dtype=np.float32)
        # Discrete action space for DQN: pick a card directly
        self.action_space = gym.spaces.Discrete(self.NR_CARDS, start=1)

    def _card_set_to_one_hot(self, card_set):
        all_cards = np.arange(1, self.NR_CARDS + 1)
        return np.isin(all_cards, card_set)
    
    # def _action_to_card(self, action, hand):
    #     # Convert the action (a probability distribution) to a card
    #     # Cards not in the hand can't be picked
    #     card_probs = action * self._card_set_to_one_hot(hand)
    #     card_index = np.argmax(card_probs)
    #     return card_index + 1  # Cards are 1-indexed

    def _get_obs(self):
        # Return a representation of the current state
        return {
            "hand": self._card_set_to_one_hot(self._agent.hand),
            "played_cards": self._card_set_to_one_hot(self._played_cards),
            "row_lengths": np.array([row.length for row in self._board.rows]),
            "row_points": np.array([row.points for row in self._board.rows]),
            "row_heads": np.array([row.head for row in self._board.rows]),
        }
    
    def _get_info(self):
        return {"board": self._board, "opponents": self._opponents, "agent": self._agent}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._board.clear()
        deck = [Card(i) for i in range(1, self.NR_CARDS + 1)]
        shuffle(deck)
        for row in self._board:
            row.add_card(deck.pop())
        for opponent in self._opponents:
            deck, hand = deck[:-self.NR_TURNS], deck[-self.NR_TURNS:]
            opponent.receive_hand(hand)
        self._agent.receive_hand(deck[-self.NR_TURNS:])

        return self._get_obs(), self._get_info()

    def step(self, action):
        # Execute one time step within the environment
        reward = 0
        # Determine what cards the agent and the opponents play
        played_cards: dict[Player, Card] = dict()
        # card = self._action_to_card(action, self.agent.hand)
        card = Card(action)
        if not card in self._agent.hand:
            # invalid card: pick a random valid card instead
            card = Card(self.np_random.choice(self._agent.hand))
            reward -= 20  # Penalty for invalid action
        self._agent.hand.remove(card)
        played_cards[self._agent] = card
        for opponent in self._opponents:
            card = opponent.choose_card(self._board)
            opponent.hand.remove(card)
            played_cards[opponent] = card
        # reverse lookup to find which opponent played which card
        card_players: dict[Card, Player] = {card : player for player, card in played_cards.items()}
        cards = list(played_cards.values())
        cards.sort()
        for card in cards:
            player = card_players[card]
            points = self._board.play_card(card)
            if points == -1:
                row_index = player.choose_row(self._board)
                points = self._board.clear_row(row_index, card)
            player.add_points(points)
            if player is self._agent:
                # TODO: opponents getting points could also lead to positive reward
                reward -= points  # Negative points as reward
        self._played_cards.extend(cards)

        terminated = len(self._agent.hand) == 0
        truncated = False
        observation = self._get_obs()
        info = self._get_info()
        return observation, reward, terminated, truncated, info
