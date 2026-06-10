import { useState, useEffect } from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell,
  BarChart, Bar,
} from "recharts";
import {
  ShieldAlert, Clock, AlertTriangle, BookX,
  RefreshCw, TrendingUp, Activity, BarChart3,
  MessageSquareWarning, Eye, ChevronRight,
  Users,
} from "lucide-react";
import { API_BASE, authFetch } from "../config";

function tooltipStyle() {
  const isLight = document.documentElement.getAttribute("data-theme") === "light";
  return {
    background: isLight ? "#fff" : "#0F1422",
    border: isLight ? "1px solid rgba(0,0,0,0.08)" : "1px solid rgba(255,255,255,0.08)",
    borderRadius: 8,
    fontSize: 12,
    color: isLight ? "#0F172A" : "#E2E8F0",
  };
}

function gridStroke() {
  const isLight = document.documentElement.getAttribute("data-theme") === "light";
  return isLight ? "rgba(0,0,0,0.04)" : "rgba(255,255,255,0.04)";
}

const LABEL_COLORS = {
  clean:          "#22c55e",
  cyberbullying:  "#f59e0b",
  harassment:     "#ef4444",
  hate_speech:    "#dc2626",
  threat:         "#991b1b",
  religious_hate: "#7c3aed",
};

const SEVERITY_COLORS = {
  critical: "#ef4444",
  high:     "#f97316",
  medium:   "#eab308",
  low:      "#22c55e",
};

const SEVERITY_ICONS = {
  critical: AlertTriangle,
  high:     AlertTriangle,
  medium:   Clock,
  low:      Activity,
};

function StatCard({ icon: Icon, label, value, accent, trend }) {
  return (
    <div className="stat-card" style={{ "--accent": accent }}>
      <div className="stat-icon-wrap" style={{ background: `${accent}15` }}>
        <Icon size={20} color={accent} strokeWidth={1.8} />
      </div>
      <div className="stat-body">
        <span className="stat-label">{label}</span>
        <span className="stat-value">{value ?? "--"}</span>
      </div>
      {trend != null && (
        <div className={`stat-trend ${trend >= 0 ? "up" : "down"}`}>
          <TrendingUp size={14} />
          {Math.abs(trend)}%
        </div>
      )}
    </div>
  );
}

function SeverityBadge({ level }) {
  const Icon = SEVERITY_ICONS[level] || Activity;
  return (
    <span className="sev-badge" style={{ color: SEVERITY_COLORS[level], background: `${SEVERITY_COLORS[level]}18` }}>
      <Icon size={12} />
      {level}
    </span>
  );
}

function CategoryLegend({ label, count, total, color }) {
  const pct = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
  return (
    <div className="cat-legend-item">
      <span className="cat-dot" style={{ background: color }} />
      <span className="cat-name">{label.replace(/_/g, " ")}</span>
      <span className="cat-pct">{pct}%</span>
      <span className="cat-count">{count}</span>
    </div>
  );
}

function EmptyState({ icon: Icon, title, message }) {
  return (
    <div className="empty-state">
      <Icon size={40} strokeWidth={1} />
      <h4>{title}</h4>
      <p>{message}</p>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="page">
      <div className="skel-header" />
      <div className="skel-grid">
        {[1, 2, 3, 4].map(i => <div key={i} className="skel-card" />)}
      </div>
      <div className="skel-chart" />
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats]           = useState(null);
  const [recent, setRecent]         = useState([]);
  const [timeseries, setTimeseries] = useState([]);
  const [activity, setActivity]     = useState({ top_users: [], by_platform: {}, by_severity: {} });
  const [loading, setLoading]       = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  async function safeJson(url) {
    try {
      const res = await authFetch(url);
      if (!res.ok) return null;
      return await res.json();
    } catch { return null; }
  }

  async function fetchData(silent = false) {
    if (!silent) setLoading(true);
    setRefreshing(true);
    try {
      const [s, r, t, a] = await Promise.all([
        safeJson(`${API_BASE}/dashboard/stats`),
        safeJson(`${API_BASE}/dashboard/recent?limit=6`),
        safeJson(`${API_BASE}/dashboard/timeseries?hours=24`),
        safeJson(`${API_BASE}/moderation/user-activity`),
      ]);
      setStats(s);
      setRecent(r?.items || []);
      const points = (t?.points || []).map(p => ({
        hour: p.hour.slice(11, 16),
        ...p.by_label,
      }));
      setTimeseries(points);
      setActivity(a || { top_users: [], by_platform: {}, by_severity: {} });
    } catch {
      setStats(null);
      setRecent([]);
      setTimeseries([]);
      setActivity({ top_users: [], by_platform: {}, by_severity: {} });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => { fetchData(); }, []);

  if (loading) return <LoadingSkeleton />;

  const dist      = stats?.label_distribution    || {};
  const sevDist   = stats?.severity_distribution || {};
  const totalFlag = stats?.total_flagged || 0;
  const pending   = stats?.pending_moderation || 0;
  const critical  = sevDist.critical || 0;
  const religious = dist.religious_hate || 0;

  const chartLabels = ["cyberbullying", "harassment", "hate_speech", "threat", "religious_hate"];

  const pieData = Object.entries(dist)
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name: name.replace(/_/g, " "), value, color: LABEL_COLORS[name] || "#64748b" }));

  const totalCategory = Object.values(dist).reduce((a, b) => a + b, 0);

  return (
    <div className="page dashboard-page">
      {/* Header */}
      <div className="dash-header">
        <div>
          <h1 className="page-title">Monitoring Dashboard</h1>
          <p className="page-sub">Real-time cyberbullying detection overview</p>
        </div>
        <button
          className={`btn-refresh ${refreshing ? "spinning" : ""}`}
          onClick={() => fetchData(true)}
          disabled={refreshing}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {/* Stat Cards */}
      <div className="stat-grid">
        <StatCard
          icon={ShieldAlert}
          label="Total Flagged"
          value={totalFlag}
          accent="#ef4444"
        />
        <StatCard
          icon={Clock}
          label="Pending Review"
          value={pending}
          accent="#f59e0b"
        />
        <StatCard
          icon={AlertTriangle}
          label="Critical Threats"
          value={critical}
          accent="#dc2626"
        />
        <StatCard
          icon={BookX}
          label="Religious Hate"
          value={religious}
          accent="#7c3aed"
        />
      </div>

      {/* Chart + Pie */}
      <div className="chart-row">
        {/* Area Chart */}
        <div className="card chart-card">
          <div className="card-head">
            <div className="card-head-left">
              <Activity size={16} />
              <span>Flag Activity</span>
            </div>
            <span className="card-head-sub">Last 24 hours</span>
          </div>
          {timeseries.length === 0 ? (
            <EmptyState
              icon={BarChart3}
              title="No activity data"
              message="Flags will appear here once content is analyzed."
            />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={timeseries} margin={{ top: 4, right: 12, left: -24, bottom: 0 }}>
                <defs>
                  {chartLabels.map(lbl => (
                    <linearGradient key={lbl} id={`g-${lbl}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor={LABEL_COLORS[lbl]} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={LABEL_COLORS[lbl]} stopOpacity={0} />
                    </linearGradient>
                  ))}
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={gridStroke()} />
                <XAxis dataKey="hour" tick={{ fill: "var(--text-dim)", fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "var(--text-dim)", fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={tooltipStyle()}
                  labelStyle={{ color: "var(--text-muted)" }}
                />
                {chartLabels.map(lbl => (
                  <Area
                    key={lbl}
                    type="monotone"
                    dataKey={lbl}
                    stroke={LABEL_COLORS[lbl]}
                    fill={`url(#g-${lbl})`}
                    strokeWidth={1.5}
                    dot={false}
                    name={lbl.replace(/_/g, " ")}
                  />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Pie + Legend */}
        <div className="card pie-card">
          <div className="card-head">
            <div className="card-head-left">
              <BarChart3 size={16} />
              <span>Category Breakdown</span>
            </div>
          </div>
          {pieData.length === 0 ? (
            <EmptyState
              icon={BarChart3}
              title="No categories yet"
              message="Category distribution will show after analysis."
            />
          ) : (
            <div className="pie-wrap">
              <ResponsiveContainer width={160} height={160}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={48}
                    outerRadius={72}
                    paddingAngle={2}
                    dataKey="value"
                    stroke="none"
                  >
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={tooltipStyle()}
                    formatter={(val, name) => [`${val} (${((val / totalCategory) * 100).toFixed(1)}%)`, name]}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="pie-legend">
                {pieData.map(d => (
                  <CategoryLegend
                    key={d.name}
                    label={d.name}
                    count={d.value}
                    total={totalCategory}
                    color={d.color}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Severity + Recent + User Activity */}
      <div className="bottom-row">
        {/* Severity */}
        <div className="card sev-card">
          <div className="card-head">
            <div className="card-head-left">
              <AlertTriangle size={16} />
              <span>Severity Levels</span>
            </div>
          </div>
          <div className="sev-list">
            {["critical", "high", "medium", "low"].map(key => {
              const count = sevDist[key] || 0;
              const maxSev = Math.max(...Object.values(sevDist), 1);
              const pct = (count / maxSev) * 100;
              return (
                <div className="sev-row" key={key}>
                  <SeverityBadge level={key} />
                  <div className="sev-track">
                    <div
                      className="sev-fill"
                      style={{ width: `${pct}%`, background: SEVERITY_COLORS[key] }}
                    />
                  </div>
                  <span className="sev-count">{count}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent flags */}
        <div className="card recent-card">
          <div className="card-head">
            <div className="card-head-left">
              <MessageSquareWarning size={16} />
              <span>Recent Flags</span>
            </div>
          </div>
          {recent.length === 0 ? (
            <EmptyState
              icon={Eye}
              title="No recent flags"
              message="Flagged content will appear here in real-time."
            />
          ) : (
            <div className="recent-list">
              {recent.map((item, i) => (
                <div className="recent-row" key={i}>
                  <span className="recent-dot" style={{ background: LABEL_COLORS[item.label] || "#64748b" }} />
                  <div className="recent-body">
                    <span className="recent-cat">{item.label?.replace(/_/g, " ")}</span>
                    <span className="recent-text">{item.text?.slice(0, 72)}</span>
                  </div>
                  <span className="recent-conf">{(item.confidence * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* User Activity */}
      <div className="bottom-row" style={{ marginTop: 14 }}>
        {/* Top flagged users */}
        <div className="card activity-card">
          <div className="card-head">
            <div className="card-head-left">
              <Users size={16} />
              <span>Top Flagged Users</span>
            </div>
          </div>
          {activity.top_users.length === 0 ? (
            <EmptyState icon={Users} title="No user data" message="User activity will appear after flags are recorded." />
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={activity.top_users} layout="vertical" margin={{ top: 0, right: 12, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridStroke()} horizontal={false} />
                <XAxis type="number" tick={{ fill: "var(--text-dim)", fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="author" type="category" width={100} tick={{ fill: "var(--text-muted)", fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={tooltipStyle()}
                  formatter={(val) => [`${val} flags`, "Count"]}
                />
                <Bar dataKey="count" fill="#ef4444" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Platform breakdown */}
        <div className="card activity-card">
          <div className="card-head">
            <div className="card-head-left">
              <BarChart3 size={16} />
              <span>Platform Breakdown</span>
            </div>
          </div>
          {Object.keys(activity.by_platform).length === 0 ? (
            <EmptyState icon={BarChart3} title="No platform data" message="Platform distribution will appear after analysis." />
          ) : (
            <div className="platform-list">
              {Object.entries(activity.by_platform).map(([platform, count]) => {
                const total = Object.values(activity.by_platform).reduce((a, b) => a + b, 0);
                const pct = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
                return (
                  <div className="platform-row" key={platform}>
                    <span className="platform-name">{platform || "unknown"}</span>
                    <div className="platform-track">
                      <div className="platform-fill" style={{ width: `${pct}%` }} />
                    </div>
                    <span className="platform-count">{count} ({pct}%)</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
