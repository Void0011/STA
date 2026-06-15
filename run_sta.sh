#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$root_dir/build" "$root_dir/reports"

cd "$root_dir"
yosys -q -s scripts/synth.ys -l reports/yosys.log
sta -exit scripts/sta.tcl | tee reports/sta.log
