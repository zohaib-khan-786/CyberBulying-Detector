import { useState, useEffect } from "react";
import { authFetch, getCurrentUser, API_BASE } from "../config";

export default function Users() {
  const [users, setUsers]       = useState([]);
  const [total, setTotal]       = useState(0);
  const [page, setPage]         = useState(1);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState("");
  const [actionMsg, setActionMsg] = useState("");
  const currentUser = getCurrentUser();
  const isAdmin = currentUser?.role === "admin";

  useEffect(() => {
    fetchUsers();
  }, [page]);

  async function fetchUsers() {
    setLoading(true);
    setError("");
    try {
      const res = await authFetch(`${API_BASE}/auth/users?page=${page}&per_page=20`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to load users");
      setUsers(data.users);
      setTotal(data.total);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function changeRole(userId, newRole) {
    setActionMsg("");
    try {
      const res = await authFetch(`${API_BASE}/auth/users/${userId}/role`, {
        method:  "PATCH",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ role: newRole }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed");
      setActionMsg(`User @${data.user.username} role changed to ${newRole}`);
      fetchUsers();
    } catch (err) {
      setActionMsg(err.message);
    }
  }

  async function toggleActive(userId, activate) {
    setActionMsg("");
    const endpoint = activate ? "activate" : "deactivate";
    try {
      const res = await authFetch(`${API_BASE}/auth/users/${userId}/${endpoint}`, {
        method: "POST",
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed");
      setActionMsg(`User @${data.user.username} ${endpoint}d`);
      fetchUsers();
    } catch (err) {
      setActionMsg(err.message);
    }
  }

  if (!isAdmin) {
    return (
      <div className="page">
        <h2>Users</h2>
        <p className="muted">Admin access required to manage users.</p>
        <div className="user-self-card">
          <h3>Your Profile</h3>
          <table className="detail-table">
            <tbody>
              <tr><td>Username</td><td><strong>{currentUser?.username}</strong></td></tr>
              <tr><td>Email</td><td>{currentUser?.email}</td></tr>
              <tr><td>Role</td><td><span className="badge">{currentUser?.role}</span></td></tr>
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2>User Management</h2>
        <span className="muted">{total} registered users</span>
      </div>

      {actionMsg && <div className="toast">{actionMsg}</div>}
      {error && <div className="error-box">{error}</div>}

      {loading ? (
        <p>Loading users…</p>
      ) : (
        <>
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Joined</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id} className={u.id === currentUser?.id ? "row-self" : ""}>
                  <td>{u.id}</td>
                  <td>
                    <strong>@{u.username}</strong>
                    {u.id === currentUser?.id && <span className="badge badge-you">you</span>}
                  </td>
                  <td className="muted">{u.email}</td>
                  <td>
                    <span className={`badge ${u.role === "admin" ? "badge-admin" : "badge-user"}`}>
                      {u.role}
                    </span>
                  </td>
                  <td>
                    <span className={`status-dot ${u.is_active ? "active" : "inactive"}`} />
                    {u.is_active ? "Active" : "Inactive"}
                  </td>
                  <td className="muted">
                    {u.created_at ? new Date(u.created_at * 1000).toLocaleDateString() : "—"}
                  </td>
                  <td className="actions-cell">
                    {u.id !== currentUser?.id && (
                      <>
                        {u.role === "user" ? (
                          <button
                            className="btn-sm btn-outline"
                            onClick={() => changeRole(u.id, "admin")}
                            title="Promote to admin"
                          >
                            Promote
                          </button>
                        ) : (
                          <button
                            className="btn-sm btn-outline"
                            onClick={() => changeRole(u.id, "user")}
                            title="Demote to user"
                          >
                            Demote
                          </button>
                        )}
                        {u.is_active ? (
                          <button
                            className="btn-sm btn-danger"
                            onClick={() => toggleActive(u.id, false)}
                            title="Deactivate user"
                          >
                            Deactivate
                          </button>
                        ) : (
                          <button
                            className="btn-sm btn-success"
                            onClick={() => toggleActive(u.id, true)}
                            title="Activate user"
                          >
                            Activate
                          </button>
                        )}
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {total > 20 && (
            <div className="pagination">
              <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</button>
              <span>Page {page}</span>
              <button disabled={users.length < 20} onClick={() => setPage(p => p + 1)}>Next</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
