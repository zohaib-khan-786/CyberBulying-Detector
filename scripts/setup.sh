#!/usr/bin/env bash
# setup.sh — One-command local dev setup
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${GREEN}=== CyberGuard — Setup ===${NC}\n"

# 1. .env
if [ ! -f .env ]; then
  cp .env.example .env
  echo -e "${YELLOW}[!] Created .env from .env.example — edit it with your API keys.${NC}"
fi

# 2. Python venv
if [ ! -d venv ]; then
  echo "Creating Python virtual environment…"
  python3 -m venv venv
fi
source venv/bin/activate
echo "Installing backend dependencies…"
pip install -q -r backend/requirements.txt

# 3. Train model (uses synthetic demo data if no CSV provided)
echo -e "\nTraining ML model (demo data)…"
python ml_pipeline/train.py
echo -e "${GREEN}✓ Model trained${NC}"

# 4. Frontend
echo -e "\nInstalling frontend dependencies…"
cd frontend && npm install --silent && cd ..
echo -e "${GREEN}✓ Frontend ready${NC}"

echo -e "\n${GREEN}=== Setup complete! ===${NC}"
echo ""
echo "  Start backend:   source venv/bin/activate && python backend/app.py"
echo "  Start frontend:  cd frontend && npm run dev"
echo ""
echo "  Or use Docker:   docker-compose up --build"
echo ""
