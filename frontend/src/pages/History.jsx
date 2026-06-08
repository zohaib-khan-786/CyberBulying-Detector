import { useState, useEffect } from "react";
import {
  Trash2, AlertTriangle, Ban, CheckCircle2,
  X, ChevronLeft, ChevronRight,
  ShieldAlert, ShieldCheck, ShieldQuestion,
  Download, Square, CheckSquare,
} from "lucide-react";
import { API_BASE, authFetch } from "../config";

const LABEL_COLORS = {
  clean:          "#22c55e",
  cyberbullying:  "#f97316",
  harassment:     "#ef4444",
  hate_speech:    "#dc2626",
  threat:         "#7f1d1d",
  religious_hate: "#7c3aed",
};

const SEVERITY_META = {
  none:     { color: "#22c55e", icon: ShieldCheck },
  low:      { color: "#86efac", icon: ShieldCheck },
  medium:   { color: "#fbbf24", icon: ShieldQuestion },
  high:     { color: "#f97316", icon: ShieldAlert },
  critical: { color: "#ef4444", icon: ShieldAlert },
};

const ACTION_META = {
  delete:  { label: "Delete",  icon: Trash2,        desc: "Log deletion (call Meta API to remove)", color: "#ef4444" },
  warn:    { label: "Warn",    icon: AlertTriangle,  desc: "Record warning against this user",        color: "#f97316" },
  block:   { label: "Block",   icon: Ban,            desc: "Permanently block this user",              color: "#dc2626" },
  dismiss: { label: "Dismiss", icon: CheckCircle2,   desc: "Mark as reviewed, no action needed",       color: "#64748b" },
};

function ModerationModal({ flag, onClose, onSuccess }) {
  const [action, setAction]   = useState("warn");
  const [note, setNote]       = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  async function submit() {
    setLoading(true);
    setError("");
    try {
      const res = await authFetch(`${API_BASE}/moderation/action`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ flag_id: flag.id, action, note }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Action failed");
      onSuccess(data.message);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <span>Moderate Flag #{flag.id}</span>
          <button className="modal-close" onClick={onClose}><X size={16} /></button>
        </div>

        <div className="modal-body">
          <div className="modal-flag-preview">
            <span className="hist-label" style={{ color: LABEL_COLORS[flag.label] }}>
              {flag.label?.replace(/_/g, " ")}
            </span>
            <span className="modal-author">@{flag.author || "unknown"}</span>
          </div>
          <p className="modal-text">"{flag.text?.slice(0, 200)}"</p>

          {flag.trigger_words && flag.trigger_words.length > 0 && (
            <div className="modal-trigger">
              <span className="modal-trigger-label">Trigger Words:</span>
              {flag.trigger_words.map((w, i) => (
                <span key={i} className="modal-trigger-word" style={{ color: LABEL_COLORS[flag.label], borderColor: LABEL_COLORS[flag.label] }}>
                  {w}
                </span>
              ))}
            </div>
          )}

          <div className="action-grid">
            {Object.entries(ACTION_META).map(([key, meta]) => {
              const Icon = meta.icon;
              return (
                <button
                  key={key}
                  className={`action-btn ${action === key ? "active" : ""}`}
                  style={action === key ? { borderColor: meta.color, color: meta.color } : {}}
                  onClick={() => setAction(key)}
                >
                  <Icon size={16} />
                  <span className="action-label">{meta.label}</span>
                  <span className="action-desc">{meta.desc}</span>
                </button>
              );
            })}
          </div>

          <textarea
            className="text-input"
            placeholder="Optional note or reason"
            value={note}
            onChange={e => setNote(e.target.value)}
            rows={2}
          />

          {error && <div className="error-box">{error}</div>}
        </div>

        <div className="modal-footer">
          <button className="btn-ghost" onClick={onClose}>Cancel</button>
          <button
            className="btn-primary"
            style={{ background: ACTION_META[action].color }}
            onClick={submit}
            disabled={loading}
          >
            {loading ? "Applying..." : ACTION_META[action].label}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function History() {
  const [items,    setItems]    = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [filter,   setFilter]   = useState("all");
  const [page,     setPage]     = useState(1);
  const [total,    setTotal]    = useState(0);
  const [selected, setSelected] = useState(null);
  const [toast,    setToast]    = useState("");
  const [selectMode, setSelectMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);
  const [bulkLoading, setBulkLoading] = useState(false);

  const PER_PAGE = 15;

  async function fetchHistory() {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, per_page: PER_PAGE });
      if (filter !== "all") params.append("label", filter);
      const res  = await authFetch(`${API_BASE}/detect/history?${params}`);
      const data = await res.json();
      setItems(data.items || []);
      setTotal(data.total || 0);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchHistory(); }, [page, filter]);

  function showToast(msg) {
    setToast(msg);
    setTimeout(() => setToast(""), 3500);
  }

  function toggleSelect(id) {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  }

  function toggleSelectAll() {
    if (selectedIds.length === items.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(items.filter(i => i.id).map(i => i.id));
    }
  }

  async function bulkAction(action) {
    if (selectedIds.length === 0) return;
    setBulkLoading(true);
    try {
      const res = await authFetch(`${API_BASE}/moderation/bulk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ flag_ids: selectedIds, action }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Bulk action failed");
      showToast(data.message);
      setSelectedIds([]);
      setSelectMode(false);
      fetchHistory();
    } catch (e) {
      showToast(e.message);
    } finally {
      setBulkLoading(false);
    }
  }

  function exportCSV() {
    const params = new URLSearchParams();
    if (filter !== "all") params.append("label", filter);
    const url = `${API_BASE}/moderation/export?${params}`;
    window.open(url, "_blank");
  }

  function handleSuccess(msg) {
    setSelected(null);
    showToast(msg);
    fetchHistory();
  }

  const labels = ["all", "cyberbullying", "harassment", "hate_speech", "threat", "religious_hate"];

  const MOD_STATUS_COLOR = {
    pending:   "#64748b",
    actioned:  "#22c55e",
    dismissed: "#334155",
  };

  return (
    <div className="page">
      <h1 className="page-title">History & Moderation</h1>
      <p className="page-sub">All flagged content. Click any row to take a moderation action.</p>

      {toast && <div className="toast">{toast}</div>}

      <div className="filter-bar">
        {labels.map(lbl => (
          <button
            key={lbl}
            className={`filter-btn ${filter === lbl ? "active" : ""}`}
            style={filter === lbl && lbl !== "all" ? { borderColor: LABEL_COLORS[lbl], color: LABEL_COLORS[lbl] } : {}}
            onClick={() => { setFilter(lbl); setPage(1); }}
          >
            {lbl === "all" ? "All" : lbl.replace(/_/g, " ")}
          </button>
        ))}
        <span className="filter-total">{total} results</span>
      </div>

      {/* Bulk controls */}
      <div className="bulk-bar">
        <button
          className={`btn-ghost ${selectMode ? "active" : ""}`}
          onClick={() => { setSelectMode(!selectMode); setSelectedIds([]); }}
        >
          {selectMode ? <><CheckSquare size={14} /> Cancel Selection</> : <><Square size={14} /> Select Multiple</>}
        </button>

        {selectMode && (
          <>
            <button className="btn-ghost" onClick={toggleSelectAll}>
              {selectedIds.length === items.length ? "Deselect All" : "Select All"}
            </button>
            <span className="bulk-count">{selectedIds.length} selected</span>
            {selectedIds.length > 0 && (
              <>
                <button className="btn-ghost" onClick={() => bulkAction("warn")} disabled={bulkLoading}>
                  <AlertTriangle size={14} /> Warn ({selectedIds.length})
                </button>
                <button className="btn-ghost" onClick={() => bulkAction("block")} disabled={bulkLoading} style={{ color: "#dc2626" }}>
                  <Ban size={14} /> Block ({selectedIds.length})
                </button>
                <button className="btn-ghost" onClick={() => bulkAction("dismiss")} disabled={bulkLoading}>
                  <CheckCircle2 size={14} /> Dismiss ({selectedIds.length})
                </button>
              </>
            )}
          </>
        )}

        <button className="btn-ghost" onClick={exportCSV} style={{ marginLeft: "auto" }}>
          <Download size={14} /> Export CSV
        </button>
      </div>

      {loading ? (
        <div className="loading">Loading...</div>
      ) : items.length === 0 ? (
        <div className="card empty-state">
          No flagged content yet. Go to <strong>Analyze Text</strong> to start detecting.
        </div>
      ) : (
        <>
          <div className="history-table">
            <div className="history-header">
              {selectMode && <span style={{ width: 24 }} />}
              <span>Sev</span>
              <span>Category</span>
              <span>Text</span>
              <span>Conf</span>
              <span>Author</span>
              <span>Status</span>
            </div>
            {items.map((item, i) => {
              const sev = SEVERITY_META[item.severity] || SEVERITY_META.none;
              const SevIcon = sev.icon;
              const isSelected = selectedIds.includes(item.id);
              return (
                <div
                  className={`history-row clickable ${isSelected ? "row-selected" : ""}`}
                  key={item.id || i}
                  onClick={(e) => {
                    if (selectMode && item.id) {
                      e.stopPropagation();
                      toggleSelect(item.id);
                    } else if (item.id) {
                      setSelected(item);
                    }
                  }}
                  title={item.id ? "Click to moderate" : "No DB id"}
                >
                  {selectMode && (
                    <span className="select-check">
                      {isSelected ? <CheckSquare size={14} /> : <Square size={14} />}
                    </span>
                  )}
                  <span style={{ color: sev.color }}><SevIcon size={14} /></span>
                  <span className="hist-label" style={{ color: LABEL_COLORS[item.label] }}>
                    {item.label?.replace(/_/g, " ")}
                  </span>
                  <span className="hist-text" title={item.text}>
                    {item.text?.slice(0, 60)}{item.text?.length > 60 ? "..." : ""}
                  </span>
                  <span className="hist-conf">{(item.confidence * 100).toFixed(0)}%</span>
                  <span className="hist-source">@{(item.author || "--").slice(0, 12)}</span>
                  <span className="mod-badge" style={{ color: MOD_STATUS_COLOR[item.mod_status] || "#64748b" }}>
                    {item.mod_status || "--"}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="pagination">
            <button className="btn-ghost" disabled={page === 1} onClick={() => setPage(p => p - 1)}>
              <ChevronLeft size={14} /> Prev
            </button>
            <span>Page {page} of {Math.ceil(total / PER_PAGE) || 1}</span>
            <button className="btn-ghost" disabled={page * PER_PAGE >= total} onClick={() => setPage(p => p + 1)}>
              Next <ChevronRight size={14} />
            </button>
          </div>
        </>
      )}

      {selected && (
        <ModerationModal
          flag={selected}
          onClose={() => setSelected(null)}
          onSuccess={handleSuccess}
        />
      )}
    </div>
  );
}
