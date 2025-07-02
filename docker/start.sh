#!/bin/bash

# Start nginx in background
nginx -g "daemon off;" &

# Start Python API
cd /app/api
python main.py &

# Wait for both processes
wait
