#!/bin/sh
env="MPE"
scenario="simple_spread"
num_landmarks=2
num_agents=2
algo="rmappo"
exp="check"

seed=0

python onpolicy/scripts/render/render_mpe.py \
    --save_gifs \
    --env_name MPE \
    --algorithm_name rmappo \
    --experiment_name test \
    --scenario_name simple_spread \
    --num_agents 3 \
    --num_landmarks 3 \
    --seed 0 \
    --n_training_threads 1 \
    --n_rollout_threads 1 \
    --use_render \
    --use_ReLU \
    --episode_length 25 \
    --render_episodes 5 \
    --model_dir "checkpoints/models"
