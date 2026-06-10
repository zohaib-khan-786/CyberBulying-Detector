import { useState, useEffect } from "react";
import {
  Ban, AlertTriangle, ShieldCheck, ChevronLeft, ChevronRight,
  UserX, UserCheck, Clock,
} from "lucide-react";
import { API_BASE, authFetch, getCurrentUser } from "../config";

const ACTION_META = {
  warn:   { icon: AlertTriangle, color: "#f97316", label: "Warned" },
  block:  { icon: Ban,           color: "#dc2626", label: "Blocked" },
  delete: { icon: UserX,         color: "#64748b", label: "Deleted" },
};

export default function ModeratedUsers() {
  const [users, setUsers]       = useState([]);
  const [total, setTotal]       = useState(0);
  const [page, setPage]         = useState(1);
  const [loading, setLoading]   = useState(true);
  const [toast, setToast]       = useState("");
  const currentUser = getCurrentUser();
  const isAdmin = currentUser?.role === "super_admin" || currentUser?.role === "admin";

  useEffect(() => { fetchUsers(); }, [page]);

  async function fetchUsers() {
    setLoading(true);
    try {
      const res = await authFetch(`${API_BASE}/moderation/users?page=${page}&per_page=20`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed");
      setUsers(data.users || []);
      setTotal(data.total || 0);
    } catch (e) {
      setUsers([]);
    } finally {
      setLoading(false);
    }
  }

  async function liftUser(userId, username) {
    setToast("");
    try {
      const res = await authFetch(`${API_BASE}/moderation/users/${userId}/lift`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed");
      setToast(`@${username} has been reinstated.`);
      fetchUsers();
    } catch (e) {
      setToast(e.message);
    }
  }

  if (!isAdmin) {
    return (
      <div className="page">
        <h2>Moderated Users</h2>
        <p className="muted">Admin access required.</p>
      </div>
    );
  }

  return (
    <div className="page">
      <h1 className="page-title">Moderated Users</h1>
      <p className="page-sub">Users who have been warned, blocked, or deleted. Lift actions to reinstate.</p>

      {toast && <div className="toast">{toast}</div>}

      {loading ? (
        <p>Loading...</p>
      ) : users.length === 0 ? (
        <div className="card empty-state">
          <ShieldCheck size={40} strokeWidth={1} />
          <h4>No moderated users</h4>
          <p>Users will appear here after moderation actions are taken.</p>
        </div>
      ) : (
        <>
          <div className="history-table mod-table">
            <div className="history-header">
              <span>User</span>
              <span>Platform</span>
              <span>Action</span>
              <span>Reason</span>
              <span>Moderated By</span>
              <span>Date</span>
              <span>Status</span>
              <span></span>
            </div>
            {users.map((u) => {
              const meta = ACTION_META[u.action] || ACTION_META.warn;
              const Icon = meta.icon;
              return (
                <div className="history-row" key={u.id}>
                  <span className="hist-label" style={{ color: meta.color }}>@{u.username}</span>
                  <span className="muted">{u.platform || "unknown"}</span>
                  <span style={{ color: meta.color }}><Icon size={14} /> {meta.label}</span>
                  <span className="hist-text" title={u.reason}>{u.reason?.slice(0, 40)}</span>
                  <span className="muted">@{u.actioned_by}</span>
                  <span className="muted">{u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}</span>
                  <span className="mod-badge" style={{ color: u.is_active ? "#ef4444" : "#22c55e" }}>
                    {u.is_active ? "Active" : "Lifted"}
                  </span>
                  {u.is_active && (
                    <button className="btn-sm btn-success" onClick={() => liftUser(u.id, u.username)}>
                      <UserCheck size={12} /> Reinstate
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          {total > 20 && (
            <div className="pagination">
              <button className="btn-ghost" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
                <ChevronLeft size={14} /> Prev
              </button>
              <span>Page {page}</span>
              <button className="btn-ghost" disabled={users.length < 20} onClick={() => setPage(p => p + 1)}>
                Next <ChevronRight size={14} />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
