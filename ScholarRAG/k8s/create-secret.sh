#!/bin/bash
# Run this once on EC2 before applying manifests.
# Reads keys from ~/ScholarRAG/backend/.env and creates the k8s secret.

set -e

ENV_FILE="${1:-$HOME/ScholarRAG/backend/.env}"

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: .env not found at $ENV_FILE"
  echo "Usage: bash create-secret.sh [path/to/.env]"
  exit 1
fi

get_val() {
  grep -E "^$1=" "$ENV_FILE" | cut -d= -f2- | tr -d '"' | tr -d "'"
}

ANTHROPIC_API_KEY=$(get_val ANTHROPIC_API_KEY)
GITHUB_TOKEN=$(get_val GITHUB_TOKEN)
HF_TOKEN=$(get_val HF_TOKEN)
SECRET_KEY=$(get_val SECRET_KEY)

if [ -z "$ANTHROPIC_API_KEY" ] || [ -z "$SECRET_KEY" ]; then
  echo "ERROR: ANTHROPIC_API_KEY and SECRET_KEY must be set in $ENV_FILE"
  exit 1
fi

kubectl delete secret scholarrag-secret --ignore-not-found

kubectl create secret generic scholarrag-secret \
  --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  --from-literal=GITHUB_TOKEN="${GITHUB_TOKEN:-}" \
  --from-literal=HF_TOKEN="${HF_TOKEN:-}" \
  --from-literal=SECRET_KEY="$SECRET_KEY"

echo "Secret created successfully."
