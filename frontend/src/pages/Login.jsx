import { useState } from "react";
import { Shield, Sun, Moon, Activity, ShieldAlert, BarChart3 } from "lucide-react";
import { API_BASE } from "../config";

export default function Login({ onLogin, onBack }) {
  const [mode, setMode]         = useState("login");
  const [username, setUsername]   = useState("");
  const [email, setEmail]         = useState("");
  const [password, setPassword]   = useState("");
  const [tenantName, setTenantName] = useState("");
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState("");
  const [dark, setDark]           = useState(() => localStorage.getItem("theme") !== "light");

  function toggleTheme() {
    const next = !dark;
    setDark(next);
    document.documentElement.setAttribute("data-theme", next ? "dark" : "light");
    localStorage.setItem("theme", next ? "dark" : "light");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const endpoint = mode === "login" ? "/auth/login" : "/auth/register";
      const body = { username, password };
      if (mode === "register") {
        body.email = email;
        body.tenant_name = tenantName || username;
      }

      const res = await fetch(`${API_BASE}${endpoint}`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(body),
      });
      const data = await res.json();

      if (!res.ok) throw new Error(data.error || "Request failed");

      if (mode === "register") {
        const loginRes = await fetch(`${API_BASE}/auth/login`, {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body:    JSON.stringify({ username, password }),
        });
        const loginData = await loginRes.json();
        if (!loginRes.ok) throw new Error(loginData.error || "Auto-login failed");
        _storeAuth(loginData);
      } else {
        _storeAuth(data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function _storeAuth(data) {
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    localStorage.setItem("user", JSON.stringify(data.user));
    onLogin(data.user);
  }

  return (
    <div className="login-wrapper">
      {/* Theme toggle */}
      <div className="login-actions">
        <button className="login-action-btn" onClick={onBack} title="Back to home">
          &larr; Back
        </button>
        <button className="login-action-btn" onClick={toggleTheme} title={dark ? "Light mode" : "Dark mode"}>
          {dark ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      </div>

      {/* Left: Login card */}
      <div className="login-card-col">
        <div className="login-card">
          <div className="login-card-header">
            <div className="login-icon-wrap">
              <Shield size={28} strokeWidth={1.5} />
            </div>
            <h1>{mode === "login" ? "Sign in" : "Create account"}</h1>
            <p className="login-card-sub">
              {mode === "login"
                ? "Monitor and detect harmful content across your social channels."
                : "Set up your workspace to start monitoring."}
            </p>
          </div>

          <div className="login-tabs">
            <button
              className={`tab ${mode === "login" ? "active" : ""}`}
              onClick={() => { setMode("login"); setError(""); }}
            >
              Sign In
            </button>
            <button
              className={`tab ${mode === "register" ? "active" : ""}`}
              onClick={() => { setMode("register"); setError(""); }}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            <div className="field">
              <label>Username</label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="Enter username"
                required
                minLength={3}
                autoFocus
              />
            </div>

            {mode === "register" && (
              <>
                <div className="field">
                  <label>Email</label>
                  <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Enter email" required />
                </div>
                <div className="field">
                  <label>Workspace Name</label>
                  <input type="text" value={tenantName} onChange={e => setTenantName(e.target.value)} placeholder="Your company / brand name" />
                </div>
              </>
            )}

            <div className="field">
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Enter password"
                required
                minLength={8}
              />
            </div>

            {error && <div className="login-error">{error}</div>}

            <button type="submit" className="login-btn" disabled={loading}>
              {loading ? "Please wait\u2026" : mode === "login" ? "Sign In" : "Create Account"}
            </button>
          </form>
        </div>
      </div>

      {/* Right: Brand showcase */}
      <div className="login-brand-col">
        <div className="login-brand-content">
          <div className="login-brand-logo">
            <Shield size={24} strokeWidth={1.8} />
            <span>AI-Powered Cyberbullying Detection</span>
          </div>
          <h2 className="login-tagline">
            Keep your community <span className="gradient-text">safe</span> with AI moderation
          </h2>
          <p className="login-desc">
            Real-time detection of cyberbullying, hate speech, harassment, threats, and more across Facebook, Instagram, and web content.
          </p>
          <div className="login-features">
            <div className="login-feature">
              <div className="login-feat-icon" style={{ background: "rgba(239,68,68,0.12)", color: "#EF4444" }}>
                <ShieldAlert size={18} />
              </div>
              <div>
                <strong>Real-time detection</strong>
                <span>AI flags harmful content instantly</span>
              </div>
            </div>
            <div className="login-feature">
              <div className="login-feat-icon" style={{ background: "rgba(234,179,8,0.12)", color: "#EAB308" }}>
                <Activity size={18} />
              </div>
              <div>
                <strong>Multi-platform</strong>
                <span>Facebook, Instagram, web, API</span>
              </div>
            </div>
            <div className="login-feature">
              <div className="login-feat-icon" style={{ background: "rgba(59,130,246,0.12)", color: "#3B82F6" }}>
                <BarChart3 size={18} />
              </div>
              <div>
                <strong>Actionable insights</strong>
                <span>Dashboard, trends, severity analysis</span>
              </div>
            </div>
          </div>
          <p className="login-footer-text">
            Already have an account? <button className="login-text-link" onClick={() => { setMode("login"); setError(""); }}>Sign in</button>
          </p>
        </div>
      </div>
    </div>
  );
}
