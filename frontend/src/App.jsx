import { useState, useEffect, useRef, useCallback } from "react";
import {
  LayoutDashboard, Search, History as HistoryIcon,
  Radio, Users as UsersIcon, LogOut, Shield, ShieldAlert,
  Download, Settings as SettingsIcon, Menu, X, Sun, Moon,
  PanelLeftClose, PanelLeft, AlertTriangle, XCircle,
} from "lucide-react";
import { isAuthenticated, getCurrentUser, API_BASE, authFetch } from "./config";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Detector from "./pages/Detector";
import History from "./pages/History";
import Simulate from "./pages/Simulate";
import Users from "./pages/Users";
import ModeratedUsers from "./pages/ModeratedUsers";
import FetchComments from "./pages/FetchComments";
import MetaTest from "./pages/MetaTest";
import Settings from "./pages/Settings";

const TOAST_DURATION = 5000;

const labelConfig = {
  cyberbullying: { icon: AlertTriangle, color: "#EAB308", bg: "rgba(234,179,8,0.12)", border: "rgba(234,179,8,0.3)", label: "Cyberbullying" },
  harassment:    { icon: AlertTriangle, color: "#EF4444", bg: "rgba(239,68,68,0.12)", border: "rgba(239,68,68,0.3)", label: "Harassment" },
  hate_speech:   { icon: AlertTriangle, color: "#DC2626", bg: "rgba(220,38,38,0.12)", border: "rgba(220,38,38,0.3)", label: "Hate Speech" },
  threat:        { icon: AlertTriangle, color: "#991B1B", bg: "rgba(153,27,27,0.12)", border: "rgba(153,27,27,0.3)", label: "Threat" },
  clean:         { icon: AlertTriangle, color: "#22C55E", bg: "rgba(34,197,94,0.12)", border: "rgba(34,197,94,0.3)", label: "Clean" },
};

export default function App() {
  const [authed, setAuthed]          = useState(isAuthenticated());
  const [activePage, setActivePage]  = useState("dashboard");
  const [user, setUser]              = useState(getCurrentUser());
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [dark, setDark]              = useState(() => localStorage.getItem("theme") !== "light");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [toasts, setToasts]          = useState([]);

  const latestId = useRef(null);
  const toastId = useRef(0);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const addToast = useCallback((item) => {
    const id = ++toastId.current;
    const cfg = labelConfig[item.label] || labelConfig.clean;
    setToasts(prev => [...prev, { id, item, cfg }]);
    setTimeout(() => removeToast(id), TOAST_DURATION);
  }, [removeToast]);

  const fetchNotifications = useCallback(async () => {
    if (!authed) return;
    try {
      const res = await authFetch(`${API_BASE}/dashboard/recent?limit=5`);
      const data = await res.json();
      const items = data.items || [];
      if (items.length > 0) {
        const maxId = Math.max(...items.map(i => i.id));
        if (latestId.current !== null && maxId > latestId.current) {
          const newItems = items.filter(i => i.id > latestId.current);
          newItems.forEach(item => addToast(item));
        }
        latestId.current = maxId;
      }
    } catch {
    }
  }, [authed, addToast]);

  useEffect(() => {
    if (!authed) return;
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 15000);
    return () => clearInterval(interval);
  }, [authed, fetchNotifications]);

  useEffect(() => {
    setAuthed(isAuthenticated());
    setUser(getCurrentUser());
  }, []);

  useEffect(() => {
    const theme = dark ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [dark]);

  function handleLogin(loggedInUser) {
    setAuthed(true);
    setUser(loggedInUser);
    setActivePage("dashboard");
  }

  function handleLogout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    setAuthed(false);
    setUser(null);
  }

  if (!authed) {
    return <Login onLogin={handleLogin} />;
  }

  const role = user?.role || "manager";
  const isAdmin = role === "super_admin" || role === "admin";

  const pages = {
    dashboard:  <Dashboard />,
    detector:   <Detector />,
    history:    <History />,
    simulate:   <Simulate />,
    users:      <Users />,
    moderated:  <ModeratedUsers />,
    fetch:      <FetchComments />,
    metatest:   <MetaTest />,
    settings:   <Settings />,
  };

  const navItems = [
    { id: "dashboard", icon: LayoutDashboard, label: "Dashboard",  roles: ["super_admin", "admin", "manager"] },
    { id: "detector",  icon: Search,          label: "Analyze",    roles: ["super_admin", "admin", "manager"] },
    { id: "simulate",  icon: Radio,           label: "Live Feed",  roles: ["super_admin", "admin", "manager"] },
    { id: "history",   icon: HistoryIcon,     label: "History",    roles: ["super_admin", "admin", "manager"] },
    { id: "moderated", icon: ShieldAlert,     label: "Moderated",  roles: ["super_admin", "admin"] },
    { id: "fetch",     icon: Download,        label: "Fetch",      roles: ["super_admin", "admin"] },
    { id: "metatest",  icon: Shield,          label: "Meta Test",  roles: ["super_admin", "admin"] },
    { id: "settings",  icon: SettingsIcon,    label: "Settings",   roles: ["super_admin", "admin"] },
    { id: "users",     icon: UsersIcon,       label: "Users",      roles: ["super_admin", "admin"] },
  ];

  const visibleNav = navItems.filter(item => item.roles.includes(role));

  return (
    <div className={`app-shell ${sidebarCollapsed ? "sidebar-collapsed" : ""}`}>
      {mobileMenuOpen && <div className="mobile-overlay" onClick={() => setMobileMenuOpen(false)} />}

      {/* Toast Container */}
      <div className="toast-container">
        {toasts.map(t => {
          const Icon = t.cfg.icon;
          return (
            <div
              key={t.id}
              className="toast-item"
              style={{
                background: t.cfg.bg,
                borderColor: t.cfg.border,
              }}
              onClick={() => removeToast(t.id)}
            >
              <div className="toast-icon" style={{ color: t.cfg.color }}>
                <Icon size={18} />
              </div>
              <div className="toast-body">
                <div className="toast-header">
                  <span style={{ color: t.cfg.color }}>{t.cfg.label}</span>
                  <span className="toast-severity">{t.item.severity}</span>
                </div>
                <div className="toast-text">{t.item.text}</div>
                <div className="toast-meta">
                  {t.item.author && <span>@{t.item.author}</span>}
                  {t.item.platform && <span>{t.item.platform}</span>}
                </div>
              </div>
              <button className="toast-close" onClick={(e) => { e.stopPropagation(); removeToast(t.id); }}>
                <XCircle size={14} />
              </button>
            </div>
          );
        })}
      </div>

      {/* Sidebar */}
      <aside className={`sidebar ${mobileMenuOpen ? "mobile-open" : ""}`}>
        <div className="sidebar-brand">
          <div className="brand-icon-wrap">
            <Shield size={sidebarCollapsed ? 20 : 18} strokeWidth={1.8} />
          </div>
          {!sidebarCollapsed && (
            <div>
              <div className="brand-name">AI-Powered</div>
              <div className="brand-sub">Cyberbullying Detection</div>
            </div>
          )}
        </div>
        <nav className="sidebar-nav">
          {!sidebarCollapsed && <div className="nav-section-label">Main</div>}
          {visibleNav.slice(0, 4).map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              className={`nav-item ${activePage === id ? "active" : ""}`}
              onClick={() => { setActivePage(id); setMobileMenuOpen(false); }}
              title={sidebarCollapsed ? label : undefined}
            >
              <Icon size={18} strokeWidth={1.8} />
              {!sidebarCollapsed && <span>{label}</span>}
            </button>
          ))}
          {isAdmin && !sidebarCollapsed && <div className="nav-section-label">Admin</div>}
          {visibleNav.slice(4).map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              className={`nav-item ${activePage === id ? "active" : ""}`}
              onClick={() => { setActivePage(id); setMobileMenuOpen(false); }}
              title={sidebarCollapsed ? label : undefined}
            >
              <Icon size={18} strokeWidth={1.8} />
              {!sidebarCollapsed && <span>{label}</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">
              {(user?.username || "U")[0].toUpperCase()}
            </div>
            {!sidebarCollapsed && (
              <div className="user-details">
                <div className="user-name">@{user?.username || "unknown"}</div>
                <div className="user-badge">{user?.role || "user"}</div>
              </div>
            )}
          </div>
          <div className="footer-actions">
            <button className="theme-btn" onClick={() => setDark(!dark)} title={dark ? "Light mode" : "Dark mode"}>
              {dark ? <Sun size={15} /> : <Moon size={15} />}
            </button>
            <button className="logout-btn" onClick={handleLogout} title="Sign out">
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main area */}
      <main className="main-content">
        <header className="topbar">
          <div className="topbar-left">
            <button className="topbar-toggle" onClick={() => setSidebarCollapsed(!sidebarCollapsed)} title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}>
              {sidebarCollapsed ? <PanelLeft size={18} /> : <PanelLeftClose size={18} />}
            </button>
            {!sidebarCollapsed && (
              <div className="topbar-brand">
                <Shield size={16} strokeWidth={1.8} />
                <span>AI-Powered</span>
              </div>
            )}
          </div>
          <div className="topbar-right">
            <button className="topbar-btn" onClick={() => setDark(!dark)} title={dark ? "Light mode" : "Dark mode"}>
              {dark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <button className="topbar-btn topbar-logout" onClick={handleLogout} title="Sign out">
              <LogOut size={16} />
            </button>
            <div className="topbar-user">
              <div className="topbar-avatar">
                {(user?.username || "U")[0].toUpperCase()}
              </div>
              <div>
                <div className="topbar-username">@{user?.username || "unknown"}</div>
                <div className="topbar-role">{user?.role || "user"}</div>
              </div>
            </div>
          </div>
        </header>

        <div className="page">
          {pages[activePage]}
        </div>
      </main>

      <header className="mobile-header">
        <div className="mobile-brand">
          <Shield size={18} strokeWidth={1.8} />
          <span>AI-Powered</span>
        </div>
        <div className="topbar-right mobile-topbar-theme">
          <button className="topbar-btn" onClick={() => setDark(!dark)} title={dark ? "Light mode" : "Dark mode"}>
            {dark ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          <button className="mobile-hamburger" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
            {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </header>
    </div>
  );
}
