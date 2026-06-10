import { useState } from "react";
import { Shield, Sun, Moon } from "lucide-react";
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
      <div className="login-theme">
        <button className="btn-ghost" onClick={onBack} title="Back to home" style={{ padding: "6px 10px", fontSize: "0.76rem" }}>
          &larr; Home
        </button>
        <button onClick={toggleTheme} title={dark ? "Light mode" : "Dark mode"}>
          {dark ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
      <div className="login-card">
        <div className="login-brand">
          <div className="login-icon-wrap">
            <Shield size={32} strokeWidth={1.5} />
          </div>
          <h1>AI-Powered</h1>
          <p>Cyberbullying Detection</p>
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
  );
}
