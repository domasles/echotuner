# EchoTuner Documentation Dockerfile
FROM ruby:3.1-slim AS jekyll-builder

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /docs

# Copy Jekyll project files
COPY . .

# Install Ruby dependencies
RUN bundle install

# Build the Jekyll site
RUN JEKYLL_ENV=production bundle exec jekyll build

# Production stage with Nginx
FROM nginx:1.27-alpine

# Copy Jekyll build
COPY --from=jekyll-builder /docs/_site /usr/share/nginx/html

# Copy nginx configuration
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/entrypoint.sh /entrypoint.sh

# Expose the documentation port
EXPOSE 80

# Make entrypoint script executable
RUN chmod +x /entrypoint.sh

# Run the documentation site
ENTRYPOINT ["/entrypoint.sh"]
