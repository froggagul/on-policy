# ---- Base: Python 3.11 ----
FROM python:3.11-slim

# For nicer logs & faster pip
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ---- System deps (git for clone, build tools for native wheels, ffmpeg & GL libs are handy for RL/envs) ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash git build-essential cmake ffmpeg libgl1 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# ---- Clone repo ----
ARG REPO_URL="https://github.com/froggagul/on-policy"
ARG REPO_DIR="on-policy"
RUN git clone --depth 1 "$REPO_URL" "$REPO_DIR"

# ---- Install Python deps from req.txt, then the package in editable mode ----
WORKDIR /workspace/${REPO_DIR}
RUN python -m pip install --upgrade pip && \
    pip install -r req.txt && \
    pip install -e .

# ---- Default to bash so you can attach/exec easily ----
CMD ["/bin/bash"]
