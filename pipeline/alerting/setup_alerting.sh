#!/usr/bin/env bash
# Create (or update) the email alert for failed pipeline runs. Idempotent.
# Usage: ALERT_EMAIL=you@example.com ./alerting/setup_alerting.sh   (from pipeline/)
# Uses the Monitoring REST API with your gcloud login, because notification
# channels are only in gcloud's alpha component.
set -euo pipefail

PROJECT="training-performance-dashboard"
API="https://monitoring.googleapis.com/v3/projects/${PROJECT}"
CHANNEL_NAME="Pipeline alerts email"
POLICY_FILE="$(dirname "$0")/pipeline-failed-policy.json"
: "${ALERT_EMAIL:?Set ALERT_EMAIL to the address that should receive alerts}"

TOKEN="$(gcloud auth print-access-token)"
api() { curl -sS --fail-with-body -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" "$@"; }

# Reuse the channel if it already exists.
CHANNEL=$(api "${API}/notificationChannels" | python3 -c "
import json, sys
for c in json.load(sys.stdin).get('notificationChannels', []):
    if c.get('displayName') == '${CHANNEL_NAME}':
        print(c['name']); break")
if [[ -z "${CHANNEL}" ]]; then
  CHANNEL=$(api -X POST "${API}/notificationChannels" -d "{
    \"type\": \"email\", \"displayName\": \"${CHANNEL_NAME}\",
    \"labels\": {\"email_address\": \"${ALERT_EMAIL}\"}}" |
    python3 -c "import json,sys; print(json.load(sys.stdin)['name'])")
  echo "Created channel ${CHANNEL}"
fi

BODY=$(python3 -c "
import json, sys
policy = json.load(open('${POLICY_FILE}'))
policy['notificationChannels'] = ['${CHANNEL}']
print(json.dumps(policy))")
DISPLAY=$(python3 -c "import json; print(json.load(open('${POLICY_FILE}'))['displayName'])")

POLICY=$(api "${API}/alertPolicies" | python3 -c "
import json, sys
for p in json.load(sys.stdin).get('alertPolicies', []):
    if p.get('displayName') == '${DISPLAY}':
        print(p['name']); break")
if [[ -z "${POLICY}" ]]; then
  api -X POST "${API}/alertPolicies" -d "${BODY}" >/dev/null
  echo "Created alert policy '${DISPLAY}'"
else
  api -X PATCH "https://monitoring.googleapis.com/v3/${POLICY}" -d "${BODY}" >/dev/null
  echo "Updated alert policy '${DISPLAY}'"
fi
