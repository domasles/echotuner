# EchoTuner API Dockerfile
FROM python:3.12-alpine

WORKDIR /api

# Install system dependencies
RUN apk add --no-cache curl

# Copy API source code
COPY . .

# Set the API up
RUN python setup.py

# Create non-root user (use adduser for Alpine)
RUN adduser -D -s /bin/sh echotuner && chown -R echotuner:echotuner /api
USER echotuner
EXPOSE 8000

CMD ["python", "main.py"]
