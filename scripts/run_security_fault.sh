#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")/.."

RESULTS="results/security-001"
mkdir -p "$RESULTS"

CONTAINER="incident-prototype-upstream-1"
BACKEND_CONTAINER="incident-prototype-backend-1"
COMMENT="incident-prototype-security-001"

UPSTREAM_PID=$(docker inspect -f '{{.State.Pid}}' "$CONTAINER")
BACKEND_IP=$(docker inspect \
  -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
  "$BACKEND_CONTAINER")

[[ "$UPSTREAM_PID" =~ ^[1-9][0-9]*$ ]] || {
    echo "Invalid upstream PID"
    exit 1
}

[[ -n "$BACKEND_IP" ]] || {
    echo "Backend IP is missing"
    exit 1
}

# Ensure we're operating in an isolated container namespace.
HOST_NS=$(sudo readlink /proc/1/ns/net)
UPSTREAM_NS=$(sudo readlink "/proc/$UPSTREAM_PID/ns/net")

[[ "$HOST_NS" != "$UPSTREAM_NS" ]] || {
    echo "ERROR: Upstream shares host network namespace"
    exit 1
}

# Restrict the rule to the observed backend IP and TCP port.
RULE=(
  -d "$BACKEND_IP"
  -p tcp --dport 8080
  -m comment --comment "$COMMENT"
  -j DROP
)

cleanup() {
    echo
    echo "========== REMOVING EXPERIMENT RULE =========="

    if sudo nsenter -t "$UPSTREAM_PID" -n \
        iptables -C OUTPUT "${RULE[@]}" 2>/dev/null; then
        sudo nsenter -t "$UPSTREAM_PID" -n \
          iptables -D OUTPUT "${RULE[@]}"
        echo "Rule removed"
    else
        echo "Experiment rule not present"
    fi
}

# Prevent duplicate rules.
if sudo nsenter -t "$UPSTREAM_PID" -n \
    iptables -C OUTPUT "${RULE[@]}" 2>/dev/null; then
    echo "ERROR: Experiment rule already exists"
    exit 1
fi

# Register cleanup before inserting the rule.
trap cleanup EXIT

echo "========== EXPERIMENT CONFIGURATION =========="
echo "Upstream PID: $UPSTREAM_PID"
echo "Backend IP: $BACKEND_IP"
echo "Rule comment: $COMMENT"

date -u --iso-8601=seconds \
  > "$RESULTS/fault_timestamp.txt"

sudo nsenter -t "$UPSTREAM_PID" -n \
  iptables -I OUTPUT 1 "${RULE[@]}"

echo
echo "========== RULE BEFORE REQUEST =========="

sudo nsenter -t "$UPSTREAM_PID" -n \
  iptables -L OUTPUT -n -v -x --line-numbers \
  | tee "$RESULTS/iptables-before-request.txt"

echo
echo "========== UPSTREAM DEPENDENCY REQUEST =========="

curl -sS --max-time 10 \
  -o "$RESULTS/upstream-request.json" \
  -w '%{http_code}\n' \
  http://127.0.0.1:18080/request \
  | tee "$RESULTS/upstream-request-status.txt"

echo
echo "========== BACKEND HEALTH =========="

curl --fail-with-body -sS --max-time 5 \
  http://127.0.0.1:18081/health \
  | tee "$RESULTS/backend-health.json"

echo
echo
echo "========== UPSTREAM HEALTH =========="

curl --fail-with-body -sS --max-time 5 \
  http://127.0.0.1:18080/health \
  | tee "$RESULTS/upstream-health.json"

echo
echo
echo "========== RULE AFTER REQUEST =========="

sudo nsenter -t "$UPSTREAM_PID" -n \
  iptables -L OUTPUT -n -v -x --line-numbers \
  | tee "$RESULTS/iptables-after-request.txt"

echo
echo "========== APPLICATION RESPONSE =========="

python -m json.tool "$RESULTS/upstream-request.json"

docker compose logs --no-log-prefix --timestamps \
  upstream backend \
  > "$RESULTS/service-logs.txt"

date -u --iso-8601=seconds \
  > "$RESULTS/observation_timestamp.txt"

echo
echo "========== EXPERIMENT CAPTURE COMPLETE =========="
