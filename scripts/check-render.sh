#!/usr/bin/env bash
# Prove charts/odoo-manage-mcp still renders the legacy objects field for field.
#
# Renders the chart with examples/values.lyucijyun-odoo.yaml and compares the
# result, normalized (documents sorted, keys sorted), with
# tests/golden/odoo-manage-mcp.lyucijyun-odoo.yaml - the three non-Secret objects
# of the legacy k8s/08-mcp-odoo-ivnvxd-admin.yaml plus the three intended
# differences listed in that file's header.
# Exit 0 = identical, 1 = drift.
set -euo pipefail

cd "$(dirname "$0")/.."
CHART=charts/odoo-manage-mcp
GOLDEN=tests/golden/odoo-manage-mcp.lyucijyun-odoo.yaml

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

helm template mcp-odoo-admin "$CHART" \
  -n lyucijyun-odoo \
  -f "$CHART/examples/values.lyucijyun-odoo.yaml" \
  --skip-tests > "$tmp/render.yaml"

python3 scripts/normalize-manifests.py "$tmp/render.yaml" > "$tmp/render.norm.yaml"
python3 scripts/normalize-manifests.py "$GOLDEN"          > "$tmp/golden.norm.yaml"

if diff -u "$tmp/golden.norm.yaml" "$tmp/render.norm.yaml"; then
  echo "OK: chart render == $GOLDEN"
else
  echo "DRIFT: the chart no longer renders the legacy objects (see the diff above)." >&2
  exit 1
fi
