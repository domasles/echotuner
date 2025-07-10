# EchoTuner Flutter app Dockerfile
FROM alpine:3.19 AS flutter-builder

# Install dependencies
RUN apk add --no-cache curl git unzip xz zip bash gcompat

# Create flutter user
RUN adduser -D -s /bin/sh flutter

# Install Flutter as flutter user
USER flutter
ENV FLUTTER_HOME="/home/flutter"
ENV PATH="$FLUTTER_HOME/bin:$PATH"

RUN git clone https://github.com/flutter/flutter.git -b stable $FLUTTER_HOME
RUN flutter doctor --android-licenses || true
RUN flutter doctor
RUN flutter config --enable-web

WORKDIR /app
COPY --chown=flutter:flutter . .

# Install dependencies and build web
RUN flutter create .
RUN flutter pub get

RUN dart run build_runner build --delete-conflicting-outputs
RUN dart run flutter_launcher_icons

RUN flutter build web --release
RUN sed -i '/<head>/a <script src="env-config.js"></script>' /app/build/web/index.html

# Production stage with Nginx
FROM nginx:1.27-alpine

# Copy Flutter web build
COPY --from=flutter-builder /app/build/web /usr/share/nginx/html

# Copy nginx configuration
COPY docker/env-config.js.template /usr/share/nginx/html/env-config.js.template
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/entrypoint.sh /app/docker/entrypoint.sh

RUN chmod +x /app/docker/entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/app/docker/entrypoint.sh"]
