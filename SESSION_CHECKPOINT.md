# Session Checkpoint

## Changes Made
- **Forgot password UI removed** from `frontend/src/pages/Login.jsx` (back-end routes kept intact)
- **Dead CSS removed** from `frontend/src/styles.css` (`.login-forgot`, `.email-sent-msg`)
- **New Docker image built & pushed**: `zohaibkhan123/cyberguard:latest`
- **Container `cyberGuard` running** on `http://localhost:8080` → `80` (maps `$PORT`)

## To Resume
1. Open project in opencode CLI
2. Say "continue from SESSION_CHECKPOINT"
3. Remaining tasks:
   - Deploy to Cloud Run with SMTP env vars
   - Verify premium design
   - Fine-tune responsive breakpoints

## Cloud Run Deploy Command
```bash
gcloud run deploy cyberguard \
  --image zohaibkhan123/cyberguard:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="DATABASE_URL=postgresql://aipoweredcyberbullying_user:6YPpURH0i9roU8BkOuJ2y5MnbhutAbCI@dpg-d8kl8drtqb8s73eegvu0-a.singapore-postgres.render.com/aipoweredcyberbullying,SECRET_KEY=...,JWT_SECRET_KEY=...,ALLOWED_ORIGINS=https://cyberguard-xxxxx-uc.a.run.app"
```

## Run Container Locally
```powershell
docker stop cyberGuard; docker rm cyberGuard
docker run -d --name cyberGuard -p 8080:80 -e DATABASE_URL="postgresql://aipoweredcyberbullying_user:6YPpURH0i9roU8BkOuJ2y5MnbhutAbCI@dpg-d8kl8drtqb8s73eegvu0-a.singapore-postgres.render.com/aipoweredcyberbullying" zohaibkhan123/cyberguard:latest
```
