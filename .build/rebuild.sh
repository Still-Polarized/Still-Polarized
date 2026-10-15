#!/bin/sh
# Rebuild the static site from the Markdown vault.
# Run from anywhere: /mnt/workspace/hermes/still-polarized/.build/rebuild.sh
cd "$(dirname "$0")" && .venv/bin/python build.py
