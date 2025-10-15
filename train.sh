#!/bin/sh

python onpolicy/scripts/train/train_mpe.py \
    --env_name MPE \
    --algorithm_name rmappo \
    --experiment_name test \
    --scenario_name simple_spread \
    --num_agents 3 \
    --num_landmarks 3 \
    --seed 0 \
    --n_training_threads 1 \
    --n_rollout_threads 128 \
    --num_mini_batch 1 \
    --episode_length 25 \
    --num_env_steps 20000000 \
    --ppo_epoch 10 \
    --use_ReLU \
    --gain 0.01 \
    --lr 7e-4 \
    --critic_lr 7e-4 \
    --use_wandb

# adding --use_wandb means not to use wandb.. strange