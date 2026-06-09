import { useState, useEffect } from "react";
import { authFetch, getCurrentUser, API_BASE } from "../config";

export default function Users() {
  const [users, setUsers]       = useState([]);
  const [total, setTotal]       = useState(0);
  const [page, setPage]         = useState(1);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState("");
  const [actionMsg, setActionMsg] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [newUser, setNewUser] = useState({ username: "", email: "", password: "", role: "manager" });
  const currentUser = getCurrentUser();
  const isAdmin = currentUser?.role === "super_admin" || currentUser?.role === "admin";

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

  async function handleCreateUser(e) {
    e.preventDefault();
    setActionMsg("");
    try {
      const res = await authFetch(`${API_BASE}/auth/users`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newUser),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed");
      setActionMsg(`Created @${data.user.username} as ${data.user.role}`);
      setShowCreate(false);
      setNewUser({ username: "", email: "", password: "", role: "manager" });
      fetchUsers();
    } catch (err) {
      setActionMsg(err.message);
    }
  }

  async function changeRole(userId, newRole) {
    setActionMsg("");
    try {
      const res = await authFetch(`${API_BASE}/auth/users/${userId}/role`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: newRole }),
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
      const res = await authFetch(`${API_BASE}/auth/users/${userId}/${endpoint}`, { method: "POST" });
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
              <tr><td>Tenant</td><td><span className="badge">T{currentUser?.tenant_id}</span></td></tr>
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2>User Management</h2>
          <span className="muted">{total} registered users</span>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(!showCreate)}>
          {showCreate ? "Cancel" : "Add User"}
        </button>
      </div>

      {actionMsg && <div className="toast">{actionMsg}</div>}
      {error && <div className="error-box">{error}</div>}

      {showCreate && (
        <form onSubmit={handleCreateUser} className="card" style={{ padding: 20, marginBottom: 16 }}>
          <h3>Create New User</h3>
          <div className="field">
            <label>Username</label>
            <input required minLength={3} value={newUser.username} onChange={e => setNewUser(p => ({ ...p, username: e.target.value }))} />
          </div>
          <div className="field">
            <label>Email</label>
            <input required type="email" value={newUser.email} onChange={e => setNewUser(p => ({ ...p, email: e.target.value }))} />
          </div>
          <div className="field">
            <label>Password</label>
            <input required type="password" minLength={8} value={newUser.password} onChange={e => setNewUser(p => ({ ...p, password: e.target.value }))} />
          </div>
          <div className="field">
            <label>Role</label>
            <select value={newUser.role} onChange={e => setNewUser(p => ({ ...p, role: e.target.value }))}>
              <option value="manager">Manager (read-only)</option>
              <option value="admin">Admin (full access)</option>
            </select>
          </div>
          <button type="submit" className="btn btn-primary">Create User</button>
        </form>
      )}

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
                <th>Tenant</th>
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
                    <span className={`badge ${u.role === "super_admin" ? "badge-super" : u.role === "admin" ? "badge-admin" : "badge-user"}`}>
                      {u.role}
                    </span>
                  </td>
                  <td><span className="badge">T{u.tenant_id}</span></td>
                  <td>
                    <span className={`status-dot ${u.is_active ? "active" : "inactive"}`} />
                    {u.is_active ? "Active" : "Inactive"}
                  </td>
                  <td className="muted">
                    {u.created_at ? new Date(u.created_at * 1000).toLocaleDateString() : "—"}
                  </td>
                  <td className="actions-cell">
                    {u.id !== currentUser?.id && u.role !== "super_admin" && (
                      <>
                        {u.role === "manager" ? (
                          <button className="btn-sm btn-outline" onClick={() => changeRole(u.id, "admin")} title="Promote to admin">Promote</button>
                        ) : u.role === "admin" ? (
                          <button className="btn-sm btn-outline" onClick={() => changeRole(u.id, "manager")} title="Demote to manager">Demote</button>
                        ) : null}
                        {u.is_active ? (
                          <button className="btn-sm btn-danger" onClick={() => toggleActive(u.id, false)} title="Deactivate">Deactivate</button>
                        ) : (
                          <button className="btn-sm btn-success" onClick={() => toggleActive(u.id, true)} title="Activate">Activate</button>
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
