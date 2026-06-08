import { useState, useEffect } from "react";
import {
  LayoutDashboard, Search, History as HistoryIcon,
  Radio, Users as UsersIcon, LogOut, Shield, ShieldAlert,
  Download,
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

  const pages = {
    dashboard: <Dashboard />,
    detector:  <Detector />,
    history:   <History />,
    simulate:  <Simulate />,
    users:     <Users />,
    moderated: <ModeratedUsers />,
    fetch:     <FetchComments />,
    metatest:   <MetaTest />,
  };

  const navItems = [
    { id: "dashboard", icon: LayoutDashboard, label: "Dashboard" },
    { id: "detector",  icon: Search,          label: "Analyze Text" },
    { id: "history",   icon: HistoryIcon,     label: "History" },
    { id: "simulate",  icon: Radio,           label: "Live Feed" },
    { id: "users",     icon: UsersIcon,       label: "Users" },
    { id: "moderated", icon: ShieldAlert,     label: "Moderated" },
    { id: "fetch",     icon: Download,        label: "Fetch Comments" },
    { id: "metatest",  icon: Shield,          label: "Meta API Test" },
  ];

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
          {navItems.map(({ id, icon: Icon, label }) => (
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
