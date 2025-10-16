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

echo "=== Evaluating/Rendering from ${MODEL_DIR} ==="
python onpolicy/scripts/render/render_mpe.py \
  --save_gifs \
  --env_name MPE \
  --algorithm_name "${ALGO_NAME}" \
  --experiment_name "${EXPERIMENT_NAME}" \
  --scenario_name "${SCENARIO_NAME}" \
  --num_agents "${NUM_AGENTS}" \
  --num_landmarks "${NUM_LANDMARKS}" \
  --seed "${SEED}" \
  --n_training_threads 1 \
  --n_rollout_threads 1 \
  --use_render \
  --use_ReLU \
  --episode_length 25 \
  --render_episodes 5 \
  --hidden_size 16 \
  --model_dir "${MODEL_DIR}"
