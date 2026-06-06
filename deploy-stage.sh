#!/usr/bin/env bash
set -euo pipefail

REMOTE_HOST="${REMOTE_HOST:-ubuntu2}"
REMOTE_COMPONENTS_DIR="${REMOTE_COMPONENTS_DIR:-/var/homeassistant.stage/custom_components}"
REMOTE_COMPOSE_DIR="${REMOTE_COMPOSE_DIR:-/home/santiago/services/ubuntu2/home-assistant-stage}"
COMPONENT_DIR="${COMPONENT_DIR:-custom_components/saj_r5}"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_COMPONENT_DIR="${SCRIPT_DIR}/${COMPONENT_DIR}"
REMOTE_COMPONENT_DIR="${REMOTE_COMPONENTS_DIR}/$(basename "${COMPONENT_DIR}")"

if [[ ! -d "${LOCAL_COMPONENT_DIR}" ]]; then
  echo "Component directory not found: ${LOCAL_COMPONENT_DIR}" >&2
  exit 1
fi

echo "Deploying ${LOCAL_COMPONENT_DIR} to ${REMOTE_HOST}:${REMOTE_COMPONENT_DIR}"
rsync -az --delete \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  "${LOCAL_COMPONENT_DIR}/" \
  "${REMOTE_HOST}:${REMOTE_COMPONENT_DIR}/"

echo "Restarting Home Assistant container"
ssh "${REMOTE_HOST}" "cd '${REMOTE_COMPOSE_DIR}' && docker compose restart"

echo "Deployment finished. Container restart was triggered; readiness was not checked."
