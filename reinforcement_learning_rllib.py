from pprint import pprint

from ray.rllib.algorithms.dqn import DQNConfig
from ray.rllib.algorithms.sac import SACConfig
from ray.rllib.connectors.env_to_module import FlattenObservations

from players import RandomPlayer
from reinforcement_learning_environment import Take5Env

opponents = [
    RandomPlayer('Alice'),
    RandomPlayer('Bob'),
    RandomPlayer('Charlie'),
]
env_config = {"opponents": opponents}

config = (
    DQNConfig()
    # SACConfig()
    .environment(Take5Env, env_config=env_config)
    .framework("torch")
    .env_runners(
        num_env_runners=1,
        # Observations are discrete (ints) -> We need to flatten (one-hot) them.
        env_to_module_connector=lambda env: FlattenObservations()
    )
    # .training(  # SAC
    #     gamma=0.9,
    #     actor_lr=0.001,
    #     critic_lr=0.002,
    #     train_batch_size_per_learner=32,
    # )
    .training(replay_buffer_config={  # DQN
        "type": "PrioritizedEpisodeReplayBuffer",
        "capacity": 60000,
        "alpha": 0.5,
        "beta": 0.5,
    })
    .evaluation(evaluation_num_env_runners=1)
)

algo = config.build_algo()

print("Starting training...")
for _ in range(2):
    pprint(algo.train())

print("Evaluating...")
pprint(algo.evaluate())

algo.stop()