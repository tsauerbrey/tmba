#!/bin/sh

TMBA_API_URL="${TMBA_API_URL:-http://127.0.0.1:8000}"

curl \
  --silent \
  --show-error \
  --fail \
  --max-time 3 \
  --request POST \
  "${TMBA_API_URL}/airplay/session/end"