#!/usr/bin/env bash
# Build the Lambda deployment zip (function.zip) for the AWS Lambda runtime
# (Linux, python3.12, x86_64).
#
# Runs anywhere — including macOS — without Docker: pip downloads prebuilt Linux
# wheels via --platform / --only-binary instead of compiling for the host. The
# framework and example agent are pure Python and are copied in directly.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"
ZIP="$ROOT/function.zip"

# Runtime dependencies. Keep in sync with [project.dependencies] in pyproject.toml.
# (boto3 is provided by the Lambda runtime and is deliberately not bundled.)
DEPS=(
  anthropic
  requests
  "PyNaCl>=1.5.0"
  psycopg2-binary
  beautifulsoup4
  lxml
  python-dotenv
)

rm -rf "$BUILD" "$ZIP"
mkdir -p "$BUILD"

# Install dependencies as Linux x86_64 wheels for the Lambda runtime. --only-binary
# :all: guarantees no local compilation, so this produces a correct Linux package
# even when run on macOS.
python3 -m pip install --quiet --target "$BUILD" \
  --platform manylinux2014_x86_64 \
  --python-version 3.12 \
  --only-binary :all: \
  "${DEPS[@]}"

# Framework + example agent are pure Python — copy the source in directly.
cp -r "$ROOT/discord_agent" "$BUILD/discord_agent"
cp -r "$ROOT/examples" "$BUILD/examples"

# Zip the build dir contents at the archive root.
( cd "$BUILD" && zip -r -q "$ZIP" . -x '*.pyc' '*/__pycache__/*' )

echo "Built $ZIP"
