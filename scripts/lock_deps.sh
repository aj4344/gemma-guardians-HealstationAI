#!/usr/bin/env sh
# Regenerate the hash-pinned lockfiles from requirements*.txt (OPS-03).
# One universal lock covers Python 3.10-3.13 on Windows, macOS and Linux.
# Usage: sh scripts/lock_deps.sh   (needs `uv`: https://docs.astral.sh/uv/)
set -eu
cd "$(dirname "$0")/.."
for name in requirements requirements-dev; do
  uv pip compile "$name.txt" --universal --python-version 3.10 --generate-hashes \
    --no-header --output-file "$name.lock" --quiet
done
echo "Updated requirements.lock and requirements-dev.lock"
