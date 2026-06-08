import { useState } from "react";
import { AlertTriangle, CheckCircle, Search, Loader2, Globe } from "lucide-react";
import { API_BASE } from "../config";

const SEVERITY_META = {
  none:     { color: "#22c55e", label: "Safe",     bg: "#052e16" },
  low:      { color: "#86efac", label: "Low Risk", bg: "#14532d" },
  medium:   { color: "#fbbf24", label: "Medium",   bg: "#451a03" },
  high:     { color: "#f97316", label: "High",     bg: "#431407" },
  critical: { color: "#ef4444", label: "Critical", bg: "#3b0000" },
};

const LANG_NAMES = {
  en: "English", nl: "Dutch", de: "German", fr: "French",
  es: "Spanish", ur: "Urdu", ar: "Arabic", hi: "Hindi",
  tr: "Turkish", id: "Indonesian", pt: "Portuguese", it: "Italian",
};

function ScoreBar({ label, value, color }) {
  return (
    <div className="score-row">
      <span className="score-label">{label}</span>
      <div className="score-track">
        <div
          className="score-fill"
          style={{ width: `${Math.round(value * 100)}%`, background: color }}
        />
      </div>
      <span className="score-pct">{(value * 100).toFixed(1)}%</span>
    </div>
  );
}

export default function Detector() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyze() {
    if (!text.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/detect/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "API error");
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const sev = result ? SEVERITY_META[result.severity] : null;

  return (
    <div className="page">
      <h1 className="page-title">Analyze Text</h1>
      <p className="page-sub">Paste any comment, message, or post to detect harmful content.</p>

      <div className="card">
        <textarea
          className="text-input"
          placeholder="Type or paste text here..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={6}
          maxLength={5000}
        />
        <div className="input-footer">
          <span className="char-count">{text.length} / 5000</span>
          <button
            className="btn-primary"
            onClick={analyze}
            disabled={loading || !text.trim()}
          >
            {loading ? <><Loader2 size={14} className="spin" /> Analyzing...</> : <><Search size={14} /> Analyze</>}
          </button>
        </div>
      </div>

      {error && <div className="error-box">{error}</div>}

      {result && (
        <div className="result-card" style={{ borderColor: sev.color }}>
          <div className="result-header" style={{ background: sev.bg }}>
            <div>
              <div className="result-verdict" style={{ color: sev.color }}>
                {result.is_harmful
                  ? <><AlertTriangle size={16} /> Harmful Content Detected</>
                  : <><CheckCircle size={16} /> Content Appears Safe</>
                }
              </div>
              <div className="result-label">
                Category: <strong>{result.label.replace("_", " ").toUpperCase()}</strong>
                {result.detected_lang && (
                  <span className="lang-badge" title={`Confidence: ${((result.lang_confidence || 0) * 100).toFixed(0)}%`}>
                    <Globe size={10} /> {LANG_NAMES[result.detected_lang] || result.detected_lang}
                  </span>
                )}
              </div>
            </div>
            <div className="severity-badge" style={{ background: sev.color }}>
              {sev.label}
            </div>
          </div>

          <div className="result-body">
            <div className="confidence-block">
              <span className="conf-label">Confidence</span>
              <span className="conf-value" style={{ color: sev.color }}>
                {(result.confidence * 100).toFixed(1)}%
              </span>
            </div>

            <div className="scores-block">
              <div className="scores-title">Probability Distribution</div>
              {Object.entries(result.scores)
                .sort((a, b) => b[1] - a[1])
                .map(([lbl, score]) => (
                  <ScoreBar
                    key={lbl}
                    label={lbl.replace("_", " ")}
                    value={score}
                    color={lbl === result.label ? sev.color : "#334155"}
                  />
                ))}
            </div>

            {result.trigger_words && result.trigger_words.length > 0 && (
              <div className="trigger-block">
                <div className="trigger-title">Trigger Words</div>
                <div className="trigger-tags">
                  {result.trigger_words.map((word, i) => (
                    <span key={i} className="trigger-tag" style={{ background: `${sev.color}22`, color: sev.color, borderColor: sev.color }}>
                      {word}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
