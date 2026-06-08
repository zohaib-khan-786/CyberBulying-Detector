import { useState } from "react";
import {
  Download, Camera, User, Loader2,
  CheckCircle2, AlertTriangle, Globe,
} from "lucide-react";
import { API_BASE, authFetch } from "../config";

export default function FetchComments() {
  const [facebookLoading, setFacebookLoading] = useState(false);
  const [instagramLoading, setInstagramLoading] = useState(false);
  const [allLoading, setAllLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [postLimit, setPostLimit] = useState(10);
  const [commentLimit, setCommentLimit] = useState(100);

  async function fetchFacebook() {
    setFacebookLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await authFetch(
        `${API_BASE}/fetch/facebook?post_limit=${postLimit}&comment_limit=${commentLimit}`
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed");
      setResult({ platform: "facebook", ...data });
    } catch (e) {
      setError(e.message);
    } finally {
      setFacebookLoading(false);
    }
  }

  async function fetchInstagram() {
    setInstagramLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await authFetch(
        `${API_BASE}/fetch/instagram?media_limit=${postLimit}&comment_limit=${commentLimit}`
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed");
      setResult({ platform: "instagram", ...data });
    } catch (e) {
      setError(e.message);
    } finally {
      setInstagramLoading(false);
    }
  }

  async function fetchAll() {
    setAllLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await authFetch(`${API_BASE}/fetch/all`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed");
      setResult({ platform: "all", ...data });
    } catch (e) {
      setError(e.message);
    } finally {
      setAllLoading(false);
    }
  }

  const anyLoading = facebookLoading || instagramLoading || allLoading;

  return (
    <div className="page">
      <h1 className="page-title">Fetch Comments</h1>
      <p className="page-sub">
        Pull all existing comments from your Facebook Page and Instagram Account.
        Each comment will be analyzed by the AI classifier and flagged if harmful.
      </p>

      {/* Config */}
      <div className="card" style={{ marginBottom: 14 }}>
        <div className="card-head">
          <div className="card-head-left">
            <Globe size={16} />
            <span>Fetch Configuration</span>
          </div>
        </div>
        <div className="fetch-config">
          <div className="field">
            <label>Posts / Media to scan</label>
            <input
              type="number"
              className="config-input"
              value={postLimit}
              onChange={e => setPostLimit(Math.min(parseInt(e.target.value) || 1, 50))}
              min={1}
              max={50}
            />
          </div>
          <div className="field">
            <label>Max comments per post</label>
            <input
              type="number"
              className="config-input"
              value={commentLimit}
              onChange={e => setCommentLimit(Math.min(parseInt(e.target.value) || 1, 500))}
              min={1}
              max={500}
            />
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="fetch-actions">
        <button
          className="fetch-btn facebook"
          onClick={fetchFacebook}
          disabled={anyLoading}
        >
          {facebookLoading ? (
            <><Loader2 size={18} className="spin" /> Fetching...</>
          ) : (
            <><User size={18} /> Fetch Facebook Comments</>
          )}
        </button>

        <button
          className="fetch-btn instagram"
          onClick={fetchInstagram}
          disabled={anyLoading}
        >
          {instagramLoading ? (
            <><Loader2 size={18} className="spin" /> Fetching...</>
          ) : (
            <><Camera size={18} /> Fetch Instagram Comments</>
          )}
        </button>

        <button
          className="fetch-btn all"
          onClick={fetchAll}
          disabled={anyLoading}
        >
          {allLoading ? (
            <><Loader2 size={18} className="spin" /> Fetching...</>
          ) : (
            <><Download size={18} /> Fetch All Comments</>
          )}
        </button>
      </div>

      {error && <div className="error-box" style={{ marginTop: 14 }}>{error}</div>}

      {/* Result */}
      {result && (
        <div className="card" style={{ marginTop: 14 }}>
          <div className="card-head">
            <div className="card-head-left">
              {result.flagged > 0 ? (
                <AlertTriangle size={16} color="#ef4444" />
              ) : (
                <CheckCircle2 size={16} color="#22c55e" />
              )}
              <span>Fetch Complete</span>
            </div>
          </div>

          <div className="result-grid">
            <div className="result-stat">
              <span className="result-stat-label">Platform</span>
              <span className="result-stat-value" style={{ textTransform: "capitalize" }}>
                {result.platform}
              </span>
            </div>
            <div className="result-stat">
              <span className="result-stat-label">Total Comments</span>
              <span className="result-stat-value">{result.total || 0}</span>
            </div>
            <div className="result-stat">
              <span className="result-stat-label">Flagged</span>
              <span className="result-stat-value" style={{ color: result.flagged > 0 ? "#ef4444" : "#22c55e" }}>
                {result.flagged || 0}
              </span>
            </div>
          </div>

          {result.message && (
            <p style={{ marginTop: 12, fontSize: "0.85rem", color: "var(--text-muted)" }}>
              {result.message}
            </p>
          )}

          {result.details && (
            <div className="details-row">
              <div className="detail-card">
                <span className="detail-label">Facebook</span>
                <span className="detail-value">{result.details.facebook?.total || 0} comments</span>
                <span className="detail-flagged">{result.details.facebook?.flagged || 0} flagged</span>
              </div>
              <div className="detail-card">
                <span className="detail-label">Instagram</span>
                <span className="detail-value">{result.details.instagram?.total || 0} comments</span>
                <span className="detail-flagged">{result.details.instagram?.flagged || 0} flagged</span>
              </div>
            </div>
          )}

          {result.flagged > 0 && (
            <p style={{ marginTop: 12, fontSize: "0.82rem", color: "#f97316" }}>
              Flagged comments have been saved. Go to History to review and take action.
            </p>
          )}
        </div>
      )}

      {/* Instructions */}
      <div className="card" style={{ marginTop: 14 }}>
        <div className="card-head">
          <div className="card-head-left">
            <Globe size={16} />
            <span>How It Works</span>
          </div>
        </div>
        <div className="instructions">
          <div className="instruction-step">
            <span className="step-num">1</span>
            <div>
              <strong>Fetches posts</strong> from your Facebook Page or Instagram Account
            </div>
          </div>
          <div className="instruction-step">
            <span className="step-num">2</span>
            <div>
              <strong>Downloads all comments</strong> on each post
            </div>
          </div>
          <div className="instruction-step">
            <span className="step-num">3</span>
            <div>
              <strong>Runs AI classification</strong> on every comment
            </div>
          </div>
          <div className="instruction-step">
            <span className="step-num">4</span>
            <div>
              <strong>Saves flagged content</strong> to the database for moderation
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
