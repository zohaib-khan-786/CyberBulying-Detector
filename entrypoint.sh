#!/bin/bash
set -e

cd /app/backend

gunicorn app:app --bind 0.0.0.0:5000 --workers 2 --timeout 120 &
nginx -g 'daemon off;'
