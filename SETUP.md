# Local Development Setup

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** & npm
- **PostgreSQL** (or use the Render remote DB)
- **Docker** (optional, for containerized deployment)

---

## 1. Clone the Repository

```bash
git clone https://github.com/zohaib-khan-786/CyberBulying-Detector.git
cd CyberBulying-Detector
```

---

## 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Environment Variables

Create `backend/.env`:

```env
DATABASE_URL=postgresql://user:password@host:port/database
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_PAGE_ID=your_page_id
META_PAGE_ACCESS_TOKEN=your_page_access_token
META_WEBHOOK_VERIFY_TOKEN=your_verify_token
USE_TRANSFORMER=false
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

---

## 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:5173` by default (Vite).

---

## 4. Run the Backend

```bash
cd backend
python app.py
```

Or with gunicorn:

```bash
gunicorn app:app --bind 0.0.0.0:5000 --workers 2 --timeout 120
```

The API runs on `http://localhost:5000`.

---

## 5. Docker (Alternative)

```bash
# Build the full image
docker build -t cyberguard .

# Run it
docker run -d --name cyberguard -p 8080:80 \
  -e DATABASE_URL=postgresql://user:password@host:port/database \
  cyberguard
```

Visit `http://localhost:8080`.

---

## 6. Default Login

**Username:** `admin`
**Password:** `admin123`
**Role:** super_admin

---

## 7. Webhook Testing (ngrok)

```bash
ngrok http 5000
```

Set the ngrok URL as your webhook callback in Meta Developer Portal:
```
https://your-ngrok-url.ngrok-free.app/api/webhook/meta
```
