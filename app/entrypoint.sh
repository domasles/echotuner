#!/bin/sh

cat <<EOF > /usr/share/nginx/html/env-config.js
window._env_ = {
    API_HOST: "${API_HOST}",
    API_PORT: "${API_PORT}",
    DEBUG_MODE: "${DEBUG_MODE}",
    ENABLE_LOGGING: "${ENABLE_LOGGING}"
};
EOF

exec nginx -g 'daemon off;'
