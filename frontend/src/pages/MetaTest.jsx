import { useState } from "react";
import {
  CheckCircle2, XCircle, AlertTriangle, Info,
  Loader2, RefreshCw, Globe, Shield, Webhook,
} from "lucide-react";
import { API_BASE, authFetch } from "../config";

const STATUS_ICONS = {
  PASS:  <CheckCircle2 size={16} color="#22c55e" />,
  FAIL:  <XCircle size={16} color="#ef4444" />,
  WARN:  <AlertTriangle size={16} color="#f59e0b" />,
  INFO:  <Info size={16} color="#38bdf8" />,
  ERROR: <XCircle size={16} color="#ef4444" />,
};

const STATUS_COLORS = {
  PASS:  "#22c55e",
  FAIL:  "#ef4444",
  WARN:  "#f59e0b",
  INFO:  "#38bdf8",
  ERROR: "#ef4444",
};

function TestCard({ name, result }) {
  if (!result) return null;
  const icon = STATUS_ICONS[result.status] || STATUS_ICONS.INFO;
  const color = STATUS_COLORS[result.status] || "#64748b";

  return (
    <div className="test-card" style={{ borderLeftColor: color }}>
      <div className="test-header">
        {icon}
        <span className="test-name">{name}</span>
        <span className="test-status" style={{ color }}>{result.status}</span>
      </div>
      <div className="test-body">
        {result.user && <div className="test-detail"><strong>User:</strong> {result.user} (ID: {result.id})</div>}
        {result.name && <div className="test-detail"><strong>Page:</strong> {result.name} (ID: {result.id})</div>}
        {result.pages_found !== undefined && <div className="test-detail"><strong>Posts found:</strong> {result.pages_found}</div>}
        {result.count !== undefined && <div className="test-detail"><strong>Pages accessible:</strong> {result.count}</div>}
        {result.pages && result.pages.length > 0 && (
          <div className="test-detail">
            <strong>Pages:</strong>
            {result.pages.map((p, i) => (
              <div key={i} className="page-item">{p.name} ({p.id})</div>
            ))}
          </div>
        )}
        {result.granted && result.granted.length > 0 && (
          <div className="test-detail">
            <strong>Permissions ({result.granted.length}):</strong>
            <div className="perm-list">
              {result.granted.map((p, i) => (
                <span key={i} className="perm-badge">{p}</span>
              ))}
            </div>
          </div>
        )}
        {result.error && <div className="test-detail error-text"><strong>Error:</strong> {result.error}</div>}
        {result.note && <div className="test-detail note-text">{result.note}</div>}
        {result.verify_token && <div className="test-detail"><strong>Verify Token:</strong> <code>{result.verify_token}</code></div>}
      </div>
    </div>
  );
}

function ConfigItem({ label, value, set }) {
  return (
    <div className="config-item">
      <span className="config-label">{label}</span>
      <span className={`config-value ${set ? "set" : "unset"}`}>
        {set ? value : "NOT SET"}
      </span>
    </div>
  );
}

export default function MetaTest() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function runTests() {
    setLoading(true);
    setError("");
    setResults(null);
    try {
      const res = await authFetch(`${API_BASE}/fetch/test-meta`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed");
      setResults(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const tests = results?.tests || {};
  const config = results?.config || {};
  const allPassed = Object.values(tests).every(t => t.status === "PASS" || t.status === "INFO");
  const hasFailures = Object.values(tests).some(t => t.status === "FAIL" || t.status === "ERROR");

  return (
    <div className="page">
      <h1 className="page-title">Meta API & Webhook Test</h1>
      <p className="page-sub">
        Diagnose your Meta API connection, permissions, and webhook configuration.
      </p>

      <div className="card" style={{ marginBottom: 14 }}>
        <div className="card-head">
          <div className="card-head-left">
            <Globe size={16} />
            <span>Configuration</span>
          </div>
          <button className="btn-primary" onClick={runTests} disabled={loading}>
            {loading ? <><Loader2 size={14} className="spin" /> Testing...</> : <><RefreshCw size={14} /> Run All Tests</>}
          </button>
        </div>
        <div className="config-grid">
          <ConfigItem label="App ID" value={config.app_id_set ? "Set" : ""} set={config.app_id_set} />
          <ConfigItem label="App Secret" value={config.app_secret_set ? "Set" : ""} set={config.app_secret_set} />
          <ConfigItem label="Page ID" value={config.page_id} set={config.page_id !== "NOT SET"} />
          <ConfigItem label="Access Token" value={config.token_set ? "Set" : ""} set={config.token_set} />
          <ConfigItem label="Verify Token" value={config.verify_token_set ? "Set" : ""} set={config.verify_token_set} />
        </div>
      </div>

      {error && <div className="error-box" style={{ marginBottom: 14 }}>{error}</div>}

      {results && (
        <>
          <div className={`test-summary ${allPassed ? "all-pass" : hasFailures ? "has-fail" : "has-warn"}`}>
            {allPassed ? "All tests passed" : hasFailures ? "Some tests failed" : "Some warnings"}
          </div>

          <div className="test-grid">
            <TestCard name="Token Validity" result={tests.token_valid} />
            <TestCard name="Permissions" result={tests.permissions} />
            <TestCard name="Page Access (API)" result={tests.page_access} />
            <TestCard name="Direct Page Access" result={tests.direct_page} />
            <TestCard name="Page Feed Access" result={tests.page_feed} />
            <TestCard name="Webhook Configuration" result={tests.webhook_config} />
          </div>
        </>
      )}

      {!results && !loading && (
        <div className="card empty-state">
          <Shield size={40} strokeWidth={1} />
          <h4>Click "Run All Tests" to diagnose</h4>
          <p>This will test your Meta API token, permissions, page access, and webhook setup.</p>
        </div>
      )}
    </div>
  );
}
