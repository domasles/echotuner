# EchoTuner API Dockerfile
FROM python:3.12-alpine

# Install su-exec for dropping privileges
RUN apk add --no-cache su-exec

# Create api user and group
RUN addgroup api
RUN adduser -D -u 999 -G api -s /bin/sh api

# Set working directory
WORKDIR /api

# Copy API source code
COPY --chown=api:api . .

# Set the API up
RUN python setup.py

# Copy entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose the API port
EXPOSE 8000

# Use entrypoint script to fix permissions and run as api user
ENTRYPOINT ["/entrypoint.sh"]
