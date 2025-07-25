# EchoTuner Flutter web app Dockerfile
FROM alpine:3.19 AS flutter-builder

# Install dependencies
RUN apk add --no-cache curl git unzip xz zip bash gcompat

# Create flutter user
RUN addgroup flutter
RUN adduser -D -u 999 -G flutter -s /bin/sh flutter

USER flutter

ENV FLUTTER_HOME="/home/flutter"
ENV PATH="$FLUTTER_HOME/bin:$PATH"

RUN git clone https://github.com/flutter/flutter.git -b stable $FLUTTER_HOME

RUN flutter doctor
RUN flutter config --enable-web

# Set up working directory
WORKDIR /app

# Copy Flutter project files
COPY --chown=flutter:flutter . .

# Install dependencies and build web app
RUN flutter create .
RUN flutter pub get

RUN dart run build_runner build --delete-conflicting-outputs
RUN dart run flutter_launcher_icons

RUN flutter build web --release
RUN sed -i '/<head>/a <script src="env-config.js"></script>' /app/build/web/index.html

# Production stage with Nginx
FROM nginx:1.27-alpine

# Copy Flutter web app build
COPY --from=flutter-builder /app/build/web /usr/share/nginx/html

# Copy nginx configuration
COPY docker/env-config.js.template /usr/share/nginx/html/env-config.js.template
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/entrypoint.sh /entrypoint.sh

# Expose the web app port
EXPOSE 80

# Make entrypoint script executable
RUN chmod +x /entrypoint.sh

# Run the web app
ENTRYPOINT ["/entrypoint.sh"]
