"""
Cyberbullying Detector — Flask Backend
Entry point for the REST API server.
"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv( dotenv_path="../.env" )

# Suppress noisy HuggingFace/httpx INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

from models.classifier  import CyberbullyingClassifier
from models.database    import init_db, SessionLocal
from models.user        import User  # must be imported before init_db()
from routes.detect      import detect_bp
from routes.webhook     import webhook_bp
from routes.dashboard   import dashboard_bp
from routes.moderation  import moderation_bp
from routes.auth        import auth_bp
from routes.fetch_comments import fetch_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": os.getenv("ALLOWED_ORIGINS", "*")}})

# ── Database ──────────────────────────────────────────────────────────────────
init_db()
logger.info("Database initialised.")

# ── Classifier ────────────────────────────────────────────────────────────────
use_transformer = os.getenv("USE_TRANSFORMER", "false").lower() == "true"
classifier = CyberbullyingClassifier(use_transformer=use_transformer)
classifier.load()
app.config["CLASSIFIER"] = classifier

# ── Default admin user ─────────────────────────────────────────────────────────
def _ensure_admin_user():
    """Create a default admin user from env vars if no admin exists."""
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123456")
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.role == "admin").first()
        if not existing:
            admin = User(username=admin_username, email=f"{admin_username}@cyberguard.local", role="admin")
            admin.set_password(admin_password)
            db.add(admin)
            db.commit()
            logger.info("Default admin user '@%s' created.", admin_username)
    except Exception as exc:
        db.rollback()
        logger.error("Failed to create default admin: %s", exc)
    finally:
        db.close()

_ensure_admin_user()

# ── Blueprints ────────────────────────────────────────────────────────────────
app.register_blueprint(auth_bp,       url_prefix="/api/auth")
app.register_blueprint(fetch_bp,      url_prefix="/api/fetch")
app.register_blueprint(detect_bp,     url_prefix="/api/detect")
app.register_blueprint(webhook_bp,    url_prefix="/api/webhook")
app.register_blueprint(dashboard_bp,  url_prefix="/api/dashboard")
app.register_blueprint(moderation_bp, url_prefix="/api/moderation")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status":       "ok",
        "model_loaded": classifier.is_loaded,
        "model_type":   "transformer" if use_transformer else "sklearn",
        "version":      "1.1.0",
    })


@app.route("/privacy-policy")
def privacy_policy():
    """Serve privacy policy page required by Meta for app review."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Privacy Policy - CyberGuard</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #080c10; color: #e2e8f0; line-height: 1.7; padding: 40px 20px; }
    .container { max-width: 720px; margin: 0 auto; }
    h1 { font-size: 2rem; margin-bottom: 8px; color: #38bdf8; }
    h2 { font-size: 1.2rem; margin-top: 32px; margin-bottom: 12px; }
    p, li { font-size: 0.95rem; color: #94a3b8; margin-bottom: 12px; }
    ul { padding-left: 24px; }
    .updated { font-size: 0.85rem; color: #64748b; margin-bottom: 32px; }
    a { color: #38bdf8; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Privacy Policy</h1>
    <p class="updated">Last updated: May 17, 2026</p>
    <h2>1. Introduction</h2>
    <p>CyberGuard is a cyberbullying detection system that monitors and analyzes text content from social media platforms to identify harmful content. This Privacy Policy explains how we collect, use, and protect information.</p>
    <h2>2. Information We Collect</h2>
    <p>When you connect your Facebook Page or Instagram Account to CyberGuard, we collect:</p>
    <ul>
      <li><strong>Comment Text:</strong> The text content of comments on your connected social media posts</li>
      <li><strong>Comment Author:</strong> The username of the person who posted the comment</li>
      <li><strong>Platform Metadata:</strong> Platform source, timestamp, and post identifier</li>
    </ul>
    <h2>3. How We Use Your Information</h2>
    <ul>
      <li>Analyzing comments for cyberbullying, hate speech, harassment, threats, and religiously sensitive content</li>
      <li>Displaying flagged content in the admin dashboard for moderation</li>
      <li>Providing toxicity scores and severity classifications</li>
      <li>Enabling moderation actions (warn, block, delete)</li>
    </ul>
    <h2>4. Data Storage and Security</h2>
    <ul>
      <li>All data is stored securely with access controls</li>
      <li>Only authenticated administrators can access flagged content</li>
      <li>We do not sell, share, or transfer your data to third parties</li>
    </ul>
    <h2>5. Your Rights</h2>
    <p>You have the right to access, delete, and request a copy of your data. You can disconnect your accounts at any time.</p>
    <h2>6. Meta Platform Data</h2>
    <ul>
      <li>We only access data necessary for cyberbullying detection</li>
      <li>We do not use Meta data for advertising or marketing</li>
      <li>We do not transfer Meta data to data brokers</li>
      <li>We delete Meta data when no longer needed</li>
    </ul>
    <h2>7. Contact Us</h2>
    <p>Contact: <a href="mailto:privacy@cyberguard.app">privacy@cyberguard.app</a></p>
  </div>
</body>
</html>""", 200, {"Content-Type": "text/html"}


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port  = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "production") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
