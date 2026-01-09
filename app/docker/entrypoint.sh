#!/bin/sh

envsubst < /usr/share/nginx/html/env-config.js.template > /usr/share/nginx/html/env-config.js
exec su-exec nginx nginx -g 'daemon off;'
