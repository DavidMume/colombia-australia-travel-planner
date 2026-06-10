#!/usr/bin/env bash
set -euo pipefail

rm -rf dist
mkdir -p dist/data
cp -R public/. dist/
cp data/airports.csv data/verified_routes.json dist/data/

echo "Cloudflare Pages site built in dist/"
