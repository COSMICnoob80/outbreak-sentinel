#!/usr/bin/env bash
# Capture the live read-only API responses the demo video is built from.
# No POST, no payment, no money spent — every call below is a GET.
#
#   ./demo/capture_video_data.sh
#
# Writes state/video-capture/<endpoint>.json. Then run capture_video_data.py
# to compile them into snapshot.json (and add the forced-fallback weather run).
set -euo pipefail

BASE="${SENTINEL_BASE:-https://outbreak-sentinel.onrender.com}"
OUT="$(cd "$(dirname "$0")/.." && pwd)/state/video-capture"
mkdir -p "$OUT"

for ep in health telegraph/status telegraph/stats debug/weather receipts scoreboard cities risk; do
  f="$OUT/$(echo "$ep" | tr '/' '_').json"
  code=$(curl -s -m 180 -o "$f" -w '%{http_code}' "$BASE/$ep")
  printf '%-20s -> %s (%s bytes)\n' "$ep" "$code" "$(wc -c < "$f")"
  [ "$code" = "200" ] || { echo "FAILED: $ep returned $code" >&2; exit 1; }
done

echo "captured to $OUT"
