import { useState } from "react";
import { Shield } from "lucide-react";
import { API_BASE } from "../config";

export default function Login({ onLogin }) {
  const [mode, setMode]         = useState("login"); // login | register
  const [username, setUsername]   = useState("");
  const [email, setEmail]         = useState("");
  const [password, setPassword]   = useState("");
  const [tenantName, setTenantName] = useState("");
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const endpoint = mode === "login" ? "/auth/login" : "/auth/register";
      const body = { username, password };
      if (mode === "register") { body.email = email; body.tenant_name = tenantName || username; }

      const res = await fetch(`${API_BASE}${endpoint}`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(body),
      });
      const data = await res.json();

      if (!res.ok) throw new Error(data.error || "Request failed");

      if (mode === "register") {
        // Auto-login after registration
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
      <div className="login-card">
        <div className="login-brand">
          <div className="login-icon-wrap">
            <Shield size={32} strokeWidth={1.5} />
          </div>
          <h1>CyberGuard</h1>
          <p>Cyberbullying Detection System</p>
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
            {loading ? "Please wait…" : mode === "login" ? "Sign In" : "Create Account"}
          </button>
        </form>

        <p className="login-hint">
          Default admin: <code>admin</code> / <code>admin123456</code>
        </p>
      </div>
    </div>
  );
}
