#!/usr/bin/with-contenv bashio
# shellcheck shell=bash
set -euo pipefail
bashio::log.info "Starting Worldmap $(bashio::addon.version)"
cd /app
exec python3 -m worldmap
