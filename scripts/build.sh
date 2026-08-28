#!/usr/bin/env bash
# Build the Lambda deployment zip (build/function.zip).
#
# Installs the framework + its dependencies and the example agent into build/,
# then zips it. Run on Linux (or CI) so psycopg2-binary / PyNaCl resolve to
# manylinux wheels. boto3 is provided by the Lambda runtime and is not a project
# dependency, so it is not bundled.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
ZIP="$ROOT/function.zip"

rm -rf "$BUILD" "$ZIP"
mkdir -p "$BUILD"

# Framework package + dependencies.
python3 -m pip install --quiet --target "$BUILD" "$ROOT"

# The example agent lives outside the installed package; copy it in.
cp -r "$ROOT/examples" "$BUILD/examples"

# Zip the build dir contents at the archive root.
( cd "$BUILD" && zip -r -q "$ZIP" . -x '*.pyc' '*/__pycache__/*' '*.dist-info/*' )

echo "Built $ZIP"
