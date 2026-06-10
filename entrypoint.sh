#!/bin/bash
set -e

# Fresh DB for multi-tenant schema (removes old DB that lacks tenant_id columns)
rm -f /app/backend/cyberguard.db

# Substitute environment variables in nginx config (e.g. $PORT)
export PORT="${PORT:-80}"
envsubst '${PORT}' < /etc/nginx/conf.d/default.conf > /tmp/nginx.conf
mv /tmp/nginx.conf /etc/nginx/conf.d/default.conf

cd /app/backend

gunicorn app:app --bind 0.0.0.0:5000 --workers 2 --timeout 120 --preload &
nginx -g 'daemon off;'
