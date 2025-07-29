# EchoTuner API Dockerfile
FROM python:3.12-alpine

# Create api user
RUN addgroup api
RUN adduser -D -u 999 -G api -s /bin/sh api

USER api

# Set working directory
WORKDIR /api

# Copy API source code
COPY --chown=api:api . .

# Set the API up
RUN python setup.py

# Expose the API port
EXPOSE 8000

# Run the API
CMD ["python", "main.py"]
