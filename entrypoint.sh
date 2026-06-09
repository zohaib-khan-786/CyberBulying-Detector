#!/bin/bash
set -e

# Fresh DB for multi-tenant schema (removes old DB that lacks tenant_id columns)
rm -f /app/backend/cyberguard.db

cd /app/backend

gunicorn app:app --bind 0.0.0.0:5000 --workers 2 --timeout 120 --preload &
nginx -g 'daemon off;'
