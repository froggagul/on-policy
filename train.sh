#!/bin/sh
# Usage: ./run_mpe.sh <scenario_name> <algorithm_name>
#   scenario_name: simple_reference | simple_spread
#   algorithm_name: ippo | rmappo

set -eu

if [ $# -ne 2 ]; then
  echo "Usage: $0 <scenario_name: simple_reference|simple_spread> <algorithm_name: ippo|rmappo>" >&2
  exit 1
fi

SCENARIO_NAME="$1"
ALGO_NAME="$2"

# Validate scenario and set num_agents
case "$SCENARIO_NAME" in
  simple_reference)
    NUM_AGENTS=2
    ;;
  simple_spread)
    NUM_AGENTS=3
    ;;
  *)
    echo "Error: scenario_name must be one of: simple_reference, simple_spread" >&2
    exit 1
    ;;
esac

# Validate algorithm
case "$ALGO_NAME" in
  ippo|rmappo)
    ;;
  *)
    echo "Error: algorithm_name must be one of: ippo, rmappo" >&2
    exit 1
    ;;
esac

SEED=0
NUM_LANDMARKS=3
EXPERIMENT_NAME="test"  # or "${SCENARIO_NAME}-${ALGO_NAME}"
MODEL_DIR="checkpoints/${SCENARIO_NAME}/${ALGO_NAME}/models"

echo "=== Training: scenario=${SCENARIO_NAME}, algo=${ALGO_NAME}, num_agents=${NUM_AGENTS} ==="
python onpolicy/scripts/train/train_mpe.py \
  --env_name MPE \
  --algorithm_name "${ALGO_NAME}" \
  --experiment_name "${EXPERIMENT_NAME}" \
  --scenario_name "${SCENARIO_NAME}" \
  --num_agents "${NUM_AGENTS}" \
  --num_landmarks "${NUM_LANDMARKS}" \
  --seed "${SEED}" \
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
