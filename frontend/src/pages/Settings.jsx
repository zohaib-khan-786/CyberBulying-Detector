import { useState, useEffect } from "react";
import { Shield, Save, Play, CheckCircle, XCircle, Eye, EyeOff } from "lucide-react";
import { authFetch, getCurrentUser, API_BASE } from "../config";

export default function Settings() {
  const [creds, setCreds] = useState({
    app_id: "", app_secret: "", page_access_token: "",
    page_id: "", webhook_verify_token: "",
  });
  const [configured, setConfigured] = useState(false);
  const [showSecret, setShowSecret] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResults, setTestResults] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const user = getCurrentUser();

  useEffect(() => {
    loadCredentials();
  }, []);

  async function loadCredentials() {
    try {
      const res = await authFetch(`${API_BASE}/settings/meta`);
      const data = await res.json();
      if (data.configured && data.credentials) {
        setCreds(prev => ({ ...prev, ...data.credentials }));
        setConfigured(true);
      }
    } catch { /* noop */ }
  }

  function handleChange(field, value) {
    setCreds(prev => ({ ...prev, [field]: value }));
  }

  async function handleSave() {
    setSaving(true);
    setMessage("");
    setError("");
    try {
      const res = await authFetch(`${API_BASE}/settings/meta`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          app_id: creds.app_id || undefined,
          app_secret: creds.app_secret || undefined,
          page_access_token: creds.page_access_token || undefined,
          page_id: creds.page_id || undefined,
          webhook_verify_token: creds.webhook_verify_token || undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Save failed");
      setMessage("Meta credentials saved successfully.");
      setConfigured(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleTest() {
    setTesting(true);
    setTestResults(null);
    setError("");
    try {
      const res = await authFetch(`${API_BASE}/settings/meta/test`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Test failed");
      setTestResults(data.results);
    } catch (err) {
      setError(err.message);
    } finally {
      setTesting(false);
    }
  }

  const isAdmin = user?.role === "super_admin" || user?.role === "admin";

  if (!isAdmin) {
    return (
      <div className="page">
        <h2>Settings</h2>
        <p className="muted">Admin access required to configure Meta API.</p>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2>Meta API Settings</h2>
        <p className="muted">Configure your Meta (Facebook/Instagram) API credentials</p>
      </div>

      {message && <div className="toast success">{message}</div>}
      {error && <div className="error-box">{error}</div>}

      <div className="card" style={{ padding: 24 }}>
        <div className="field">
          <label>Facebook App ID</label>
          <input
            type="text"
            value={creds.app_id || ""}
            onChange={e => handleChange("app_id", e.target.value)}
            placeholder="From Meta Developer Portal"
          />
        </div>

        <div className="field">
          <label>Facebook App Secret</label>
          <div className="input-wrap">
            <input
              type={showSecret ? "text" : "password"}
              value={creds.app_secret || ""}
              onChange={e => handleChange("app_secret", e.target.value)}
              placeholder="From Meta Developer Portal"
            />
            <button className="input-suffix" onClick={() => setShowSecret(!showSecret)}>
              {showSecret ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </div>

        <div className="field">
          <label>Page Access Token</label>
          <div className="input-wrap">
            <input
              type={showSecret ? "text" : "password"}
              value={creds.page_access_token || ""}
              onChange={e => handleChange("page_access_token", e.target.value)}
              placeholder="EAAV... long-lived token"
            />
          </div>
        </div>

        <div className="field">
          <label>Facebook Page ID</label>
          <input
            type="text"
            value={creds.page_id || ""}
            onChange={e => handleChange("page_id", e.target.value)}
            placeholder="Your Facebook Page numeric ID"
          />
        </div>

        <div className="field">
          <label>Webhook Verify Token</label>
          <input
            type="text"
            value={creds.webhook_verify_token || ""}
            onChange={e => handleChange("webhook_verify_token", e.target.value)}
            placeholder="Custom string for webhook verification"
          />
        </div>

        <div className="settings-actions">
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            <Save size={16} />
            {saving ? "Saving..." : "Save Credentials"}
          </button>
          <button className="btn btn-outline" onClick={handleTest} disabled={testing}>
            <Play size={16} />
            {testing ? "Testing..." : "Test Connection"}
          </button>
        </div>
      </div>

      {testResults && (
        <div className="card" style={{ padding: 24, marginTop: 16 }}>
          <h3>Test Results</h3>
          {Object.entries(testResults).map(([key, result]) => (
            <div key={key} className="test-row">
              <span className="test-name">{key.replace(/_/g, " ")}</span>
              {result.status === "PASS" ? (
                <span className="test-pass"><CheckCircle size={14} /> {result.name || result.id || "OK"}</span>
              ) : result.status === "SKIP" ? (
                <span className="test-skip">{result.note}</span>
              ) : (
                <span className="test-fail"><XCircle size={14} /> {result.error || result.status}</span>
              )}
            </div>
          ))}
        </div>
      )}

      {configured && (
        <div className="card" style={{ padding: 24, marginTop: 16 }}>
          <h3>Webhook Setup</h3>
          <p className="muted">Set this as your webhook callback URL in Meta Developer Portal:</p>
          <code className="webhook-url">https://your-domain.com/api/webhook/meta</code>
          <p className="muted" style={{ marginTop: 8 }}>
            Verify Token: <strong>{creds.webhook_verify_token || "not set"}</strong>
          </p>
        </div>
      )}
    </div>
  );
}
