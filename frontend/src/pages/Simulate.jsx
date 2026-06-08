import { useState, useEffect, useRef } from "react";
import {
  RefreshCw, CheckCircle, Eye,
  Trash2, ChevronLeft, ChevronRight, Loader2,
} from "lucide-react";
import { API_BASE, authFetch } from "../config";

const AUTO_REFRESH_MS = 5000;

const LABEL_COLORS = {
  clean:          "#22c55e",
  cyberbullying:  "#f97316",
  harassment:     "#ef4444",
  hate_speech:    "#dc2626",
  threat:         "#7f1d1d",
  religious_hate: "#7c3aed",
};

const SEVERITY_META = {
  none:     { color: "#22c55e", label: "Safe" },
  low:      { color: "#86efac", label: "Low" },
  medium:   { color: "#fbbf24", label: "Medium" },
  high:     { color: "#f97316", label: "High" },
  critical: { color: "#ef4444", label: "Critical" },
};

export default function Simulate() {
  const [items, setItems]       = useState([]);
  const [loading, setLoading]   = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage]         = useState(1);
  const [total, setTotal]       = useState(0);
  const [toast, setToast]       = useState("");
  const [autoRefresh, setAutoRefresh] = useState(true);
  const intervalRef = useRef(null);

  const PER_PAGE = 20;

  async function fetchFlags(isAuto = false) {
    if (!isAuto) setRefreshing(true);
    try {
      const params = new URLSearchParams({ page, per_page: PER_PAGE });
      const res = await authFetch(`${API_BASE}/detect/all-flags?${params}`);
      const data = await res.json();
      setItems(data.items || []);
      setTotal(data.total || 0);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
      if (!isAuto) setRefreshing(false);
    }
  }

  useEffect(() => { fetchFlags(); }, [page]);

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(() => fetchFlags(true), AUTO_REFRESH_MS);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [autoRefresh, page]);

  async function moderateItem(id, action) {
    setToast("");
    try {
      const res = await authFetch(`${API_BASE}/moderation/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ flag_id: id, action }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed");
      setToast(data.message || `Action '${action}' completed`);
      fetchFlags();
    } catch (e) {
      setToast(e.message);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Live Feed</h1>
          <p className="page-sub">
            Real-time flagged content from Facebook and Instagram.
            Fetch comments first from the Fetch Comments page, then review here.
          </p>
        </div>
        <div className="header-actions">
          <button
            className={`btn-sm ${autoRefresh ? "btn-active" : "btn-outline"}`}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? "Auto-refresh ON" : "Auto-refresh OFF"}
          </button>
          <button
            className={`btn-refresh ${refreshing ? "spinning" : ""}`}
            onClick={() => fetchFlags()}
            disabled={refreshing}
          >
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>
      </div>

      {toast && <div className="toast">{toast}</div>}

      {loading ? (
        <p>Loading...</p>
      ) : items.length === 0 ? (
        <div className="card empty-state">
          <Eye size={40} strokeWidth={1} />
          <h4>No flagged content yet</h4>
          <p>Go to Fetch Comments to pull comments from your Facebook/Instagram pages.</p>
        </div>
      ) : (
        <>
          <div className="feed-stats">
            <span className="stat-pill">{total} total flags</span>
            <span className="stat-pill">{items.filter(i => i.is_harmful).length} harmful</span>
            <span className="stat-pill">{items.filter(i => !i.is_harmful).length} safe</span>
          </div>

          <div className="live-feed">
            {items.map((item) => {
              const sev = SEVERITY_META[item.severity] || SEVERITY_META.none;
              const catColor = LABEL_COLORS[item.label] || "#64748b";
              return (
                <div
                  key={item.id}
                  className={`feed-item ${item.is_harmful ? "harmful" : "safe"}`}
                  style={{ borderLeftColor: catColor }}
                >
                  <div className="feed-item-header">
                    <span className="feed-label" style={{ color: catColor, background: `${catColor}18` }}>
                      {item.label?.replace(/_/g, " ")}
                    </span>
                    <span className="feed-sev" style={{ color: sev.color }}>
                      {sev.label}
                    </span>
                    <span className="feed-conf">
                      {(item.confidence * 100).toFixed(0)}%
                    </span>
                    <span className="feed-platform">{item.platform || "unknown"}</span>
                  </div>

                  <p className="feed-text">{item.text}</p>

                  <div className="feed-item-footer">
                    <span className="feed-author">@{item.author || "unknown"}</span>
                    <span className="feed-time">
                      {item.created_at ? new Date(item.created_at).toLocaleString() : ""}
                    </span>
                  </div>

                  {item.trigger_words && item.trigger_words.length > 0 && (
                    <div className="feed-trigger">
                      {item.trigger_words.slice(0, 5).map((w, i) => (
                        <span key={i} className="feed-trigger-word" style={{ color: catColor, borderColor: catColor }}>
                          {w}
                        </span>
                      ))}
                    </div>
                  )}

                  {item.is_harmful && (
                    <div className="feed-actions">
                      <button className="btn-sm btn-outline" onClick={() => moderateItem(item.id, "delete")}>
                        <Trash2 size={12} /> Delete
                      </button>
                      <button className="btn-sm btn-outline" onClick={() => moderateItem(item.id, "dismiss")}>
                        <CheckCircle size={12} /> Dismiss
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="pagination">
            <button className="btn-ghost" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
              <ChevronLeft size={14} /> Prev
            </button>
            <span>Page {page} of {Math.ceil(total / PER_PAGE) || 1}</span>
            <button className="btn-ghost" disabled={page * PER_PAGE >= total} onClick={() => setPage(p => p + 1)}>
              Next <ChevronRight size={14} />
            </button>
          </div>
        </>
      )}
    </div>
  );
}
