#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "⚡ Starting PatternNest Studio on http://127.0.0.1:8092"
export PORT=8092
python3 -m src.server
