# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Stage 2: Final image — Python backend + Nginx frontend
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies (nginx + build tools for pip)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    gettext-base \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir \
    flask==3.0.3 \
    flask-cors==4.0.1 \
    gunicorn==22.0.0 \
    python-dotenv==1.0.1 \
    sqlalchemy==2.0.30 \
    scikit-learn==1.4.2 \
    numpy==1.26.4 \
    pandas==2.2.2 \
    celery==5.4.0 \
    redis==5.0.6 \
    "PyJWT>=2.8.0" \
    "bcrypt>=4.1.0" \
    "langdetect>=1.0.9" \
    requests==2.32.3 \
    "psycopg2-binary>=2.9.9" \
    && rm -rf /root/.cache/pip

RUN pip install --no-cache-dir \
    "torch>=2.0.0" --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir \
    "transformers>=4.38.0" \
    "tokenizers>=0.19.0" \
    "sentencepiece>=0.2.0" \
    "protobuf>=3.20.0" \
    && rm -rf /root/.cache/pip

# Pre-download transformer model so it's baked into the image
RUN python -c "from transformers import pipeline; pipeline('text-classification', model='gravitee-io/distilbert-multilingual-toxicity-classifier', token=None)" 2>&1 | tail -5

# Remove build tools to reduce image size
RUN apt-get purge -y --auto-remove build-essential gcc && rm -rf /var/lib/apt/lists/*

# Copy backend application code
COPY backend/ ./backend/

# Copy trained ML models (sklearn)
COPY backend/models/saved_models/*.pkl ./backend/models/saved_models/

# Copy built frontend to Nginx serve directory
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Copy Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80

CMD ["/entrypoint.sh"]
