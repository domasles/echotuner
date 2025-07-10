#!/bin/sh

[ -f /api/echotuner.db ] || touch /api/echotuner.db
[ -f /api/.cache ] || touch /api/.cache

python main.py
