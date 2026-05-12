#!/usr/bin/env bash
# Submit the robot01 pickup -> dropoff workflow to the robot01 backend.
#
# Usage:
#   ./run_pickup_dropoff.sh                 # uses robot01-backend on localhost:3001
#   BACKEND_URL=http://host:3001 ./run_pickup_dropoff.sh
#   TASK_ID=run-42 ./run_pickup_dropoff.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD_FILE="${SCRIPT_DIR}/robot01_pickup_dropoff.json"

BACKEND_URL="${BACKEND_URL:-http://localhost:3001}"
TASK_ID="${TASK_ID:-robot01-pickup-dropoff-$(date +%s)}"
TIMESTAMP="$(date +%s)"

payload=$(
  TASK_ID="$TASK_ID" TIMESTAMP="$TIMESTAMP" \
  python3 -c '
import json, os, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
data["id"] = os.environ["TASK_ID"]
data["timestamp"] = int(os.environ["TIMESTAMP"])
print(json.dumps(data))
' "$PAYLOAD_FILE"
)

echo "Submitting task ${TASK_ID} to ${BACKEND_URL}"
curl -sS -X POST "${BACKEND_URL}/api/v1/tasks" \
  -H 'Content-Type: application/json' \
  -d "$payload" | python3 -m json.tool
