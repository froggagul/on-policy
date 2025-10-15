FROM python:3.11-slim

# For nicer logs & faster pip
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash git build-essential cmake ffmpeg libgl1 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

ARG REPO_URL="https://github.com/froggagul/on-policy"
ARG REPO_DIR="on-policy"
ADD "https://api.github.com/repos/froggagul/on-policy/git/refs/heads/main" .version.json
RUN git clone "$REPO_URL" "$REPO_DIR"

WORKDIR /workspace/${REPO_DIR}
RUN python -m pip install --upgrade pip && \
    pip install -r req.txt && \
    pip install -e .

CMD ["/bin/bash"]
