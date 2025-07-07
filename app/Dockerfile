# EchoTuner Flutter App Dockerfile
FROM alpine:3.19 AS flutter-builder

# Install dependencies
RUN apk add --no-cache curl git unzip xz zip bash gcompat

# Create flutter user
RUN adduser -D -s /bin/sh flutter

# Install Flutter as flutter user
USER flutter
ENV FLUTTER_HOME="/home/flutter"
ENV PATH="$FLUTTER_HOME/bin:$PATH"

RUN git clone https://github.com/flutter/flutter.git -b stable $FLUTTER_HOME && \
    flutter doctor --android-licenses || true && \
    flutter doctor && \
    flutter config --enable-web

WORKDIR /home/flutter/app
COPY --chown=flutter:flutter . .

# Install dependencies and build web
RUN flutter pub get
RUN flutter build web --release

# Production stage with Nginx
FROM nginx:1.27-alpine

# Copy Flutter web build
COPY --from=flutter-builder /home/flutter/app/build/web /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
