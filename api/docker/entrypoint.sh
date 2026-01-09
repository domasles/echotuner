#!/bin/sh

set -e

mkdir -p /api/storage
chown -R api:api /api/storage

exec su-exec api python main.py
