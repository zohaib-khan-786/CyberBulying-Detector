import { useState, useEffect } from "react";
import {
  LayoutDashboard, Search, History as HistoryIcon,
  Radio, Users as UsersIcon, LogOut, Shield, ShieldAlert,
  Download, Settings as SettingsIcon,
} from "lucide-react";
import { isAuthenticated, getCurrentUser } from "./config";
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

export default function App() {
  const [authed, setAuthed]       = useState(isAuthenticated());
  const [activePage, setActivePage] = useState("dashboard");
  const [user, setUser]             = useState(getCurrentUser());

  useEffect(() => {
    setAuthed(isAuthenticated());
    setUser(getCurrentUser());
  }, []);

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
  const isSuperAdmin = role === "super_admin";

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
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon-wrap">
            <Shield size={20} strokeWidth={1.8} />
          </div>
          <div>
            <div className="brand-name">CyberGuard</div>
            <div className="brand-sub">Detection System</div>
          </div>
        </div>
        <nav className="sidebar-nav">
          {visibleNav.map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              className={`nav-item ${activePage === id ? "active" : ""}`}
              onClick={() => setActivePage(id)}
            >
              <Icon size={18} strokeWidth={1.8} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-info">
            <span className="user-badge">{user?.role || "user"}</span>
            <span className="user-name">@{user?.username || "unknown"}</span>
            {user?.tenant_id && <span className="user-tenant">T{user.tenant_id}</span>}
          </div>
          <button className="logout-btn" onClick={handleLogout} title="Sign out">
            <LogOut size={16} />
          </button>
        </div>
      </aside>
      <main className="main-content">{pages[activePage]}</main>
    </div>
  );
}
