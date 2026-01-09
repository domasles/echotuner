# EchoTuner Flutter web app Dockerfile
FROM ghcr.io/cirruslabs/flutter:latest AS flutter-builder

# Set up working directory
WORKDIR /app

# Copy Flutter project files
COPY --chown=flutter:flutter . .

# Install dependencies and build web app
RUN flutter create .
RUN cp samples/index.html web/index.html

RUN dart run build_runner build --delete-conflicting-outputs
RUN dart run flutter_launcher_icons

RUN flutter build web --release

# Production stage with Nginx
FROM nginx:1.27-alpine

# Copy Flutter web app build
COPY --from=flutter-builder /app/build/web /usr/share/nginx/html

# Copy nginx configuration
COPY docker/env-config.js.template /usr/share/nginx/html/env-config.js.template
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/entrypoint.sh /entrypoint.sh

# Make entrypoint script executable
RUN chmod +x /entrypoint.sh

# Expose the web app port
EXPOSE 80

# Run the web app
ENTRYPOINT ["/entrypoint.sh"]
