export const API_BASE =
  import.meta.env.VITE_API_URL || "/api";

/**
 * Authenticated fetch helper — attaches JWT from localStorage.
 * Throws on 401 to trigger login redirect.
 */
export async function authFetch(url, options = {}) {
  const token = localStorage.getItem("access_token");
  const headers = { ...(options.headers || {}) };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    window.location.reload();
    throw new Error("Session expired — please log in again.");
  }

  return res;
}

/**
 * Get the current user from localStorage.
 */
export function getCurrentUser() {
  try {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

/**
 * Check if a token exists and is not expired (basic check).
 */
export function isAuthenticated() {
  const token = localStorage.getItem("access_token");
  if (!token) return false;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp * 1000 > Date.now();
  } catch {
    return false;
  }
}
