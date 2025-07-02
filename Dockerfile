# Multi-stage Dockerfile for EchoTuner Platform
# Builds separate API and Web App images from a single Dockerfile

ARG BUILD_TARGET=all

# Stage 1: Flutter Web App Build
FROM cirrusci/flutter:3.24.5 AS flutter-builder

WORKDIR /app
COPY app/ .

# Install dependencies and build web
RUN flutter pub get
RUN flutter build web --release --web-renderer canvaskit

# Stage 2: Python API Base
FROM python:3.12-slim AS api-base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy API source code
COPY api/ .

# Create non-root user
RUN useradd --create-home --shell /bin/bash echotuner && \
    chown -R echotuner:echotuner /app

# Stage 3: API-only image
FROM api-base AS api

USER echotuner
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 4: Web App with Nginx
FROM nginx:1.27-alpine AS webapp

# Copy Flutter web build
COPY --from=flutter-builder /app/build/web /usr/share/nginx/html

# Copy nginx configuration
COPY docker/nginx-webapp.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Stage 5: Combined image with both API and Web App
FROM api-base AS combined

# Install nginx
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy Flutter web build
COPY --from=flutter-builder /app/build/web /var/www/html

# Copy nginx and supervisor configuration
COPY docker/nginx-combined.conf /etc/nginx/sites-available/default
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create directories and set permissions
RUN mkdir -p /var/log/supervisor /var/run && \
    chown -R echotuner:echotuner /app /var/www/html /var/log/supervisor

EXPOSE 80 8000

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
