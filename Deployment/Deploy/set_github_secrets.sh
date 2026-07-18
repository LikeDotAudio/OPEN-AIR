#!/usr/bin/env bash
# Push FTP/MQTT credentials from FrontEnd/.env into a GitHub Environment as
# secrets, so the deploy workflows can log in to FTPS.
#
# Prereqs:  gh CLI installed + authenticated  (gh auth login)
# Usage:    ./set_github_secrets.sh production      # or: sandbox
#
# NOTE: there is only one local .env. production and sandbox should hold
# DIFFERENT credentials — set production from your prod .env, then edit .env
# (or pass different values) before running again for sandbox.
set -euo pipefail

ENVNAME="${1:?usage: $0 <production|sandbox>}"
REPO="LikeDotAudio/OPEN-AIR"
ENV_FILE="$(cd "$(dirname "$0")/../.." && pwd)/.env"

[ -f "$ENV_FILE" ] || { echo "❌ No .env found at $ENV_FILE"; exit 1; }

# Load KEY=VALUE lines from .env into the environment
set -a; # shellcheck disable=SC1090
source "$ENV_FILE"; set +a

echo "🔧 Ensuring GitHub Environment '$ENVNAME' exists on $REPO..."
gh api -X PUT "repos/$REPO/environments/$ENVNAME" >/dev/null

for k in FTP_HOST FTP_USER FTP_PASS REMOTE_DIR \
         MQTT_HOST MQTT_PORT MQTT_USER MQTT_PASS MQTT_TOPIC; do
  v="${!k:-}"
  if [ -n "$v" ]; then
    gh secret set "$k" --env "$ENVNAME" --repo "$REPO" --body "$v"
    echo "   ✅ $k → $ENVNAME"
  fi
done

echo "🎉 Secrets set for '$ENVNAME'. Next push to that branch will deploy over FTPS."
