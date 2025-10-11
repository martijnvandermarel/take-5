from take5 import Take5
from players import *

players = [
    AscendingPlayer('Alice'),
    RandomPlayer('Bob'),
    CostFunPlayer('Charlie', num_players=4, alpha=0.4),
    DescendingPlayer('David'),
]
any_manual_players = any([isinstance(player, ManualPlayer) for player in players])
NR_ROUNDS = 1 if any_manual_players else 10000

take5 = Take5(players, quiet=(not any_manual_players))
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