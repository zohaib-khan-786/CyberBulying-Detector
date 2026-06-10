import { useState } from "react";
import { Shield, Sun, Moon, Menu, X, LogIn, AlertTriangle, BarChart3, Bell, Users, Radio, Layers, Globe, ChevronDown, ChevronRight, ArrowRight, Sparkles, ShieldCheck, Zap, TrendingUp } from "lucide-react";

export default function LandingPage({ onLoginClick }) {
  const [dark, setDark] = useState(() => localStorage.getItem("theme") !== "light");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [openFaq, setOpenFaq] = useState(null);

  function toggleTheme() {
    const next = !dark;
    setDark(next);
    document.documentElement.setAttribute("data-theme", next ? "dark" : "light");
    localStorage.setItem("theme", next ? "dark" : "light");
  }

  const features = [
    { icon: AlertTriangle, title: "AI-Powered Detection", desc: "State-of-the-art transformer models detect cyberbullying, harassment, hate speech, and threats across multiple languages with 94%+ accuracy." },
    { icon: Globe, title: "Multi-Platform Monitoring", desc: "Connect Facebook and Instagram pages via Meta API. Automatically scan comments, messages, and public posts in real time." },
    { icon: Bell, title: "Real-Time Alerts", desc: "Instant toast notifications when harmful content is detected. Color-coded by severity so you can act immediately." },
    { icon: BarChart3, title: "Advanced Analytics", desc: "Comprehensive dashboards with trend charts, severity breakdowns, platform comparisons, and actionable insights." },
    { icon: Users, title: "Multi-Tenant Teams", desc: "Super admin, admin, and manager roles. Manage multiple workspaces, assign permissions, and collaborate effectively." },
    { icon: Radio, title: "Live Feed Monitoring", desc: "Real-time comment scanning with live feed view. See new content as it's analyzed and flagged by the AI engine." },
    { icon: Layers, title: "Smart Classification", desc: "Seven-label classification: cyberbullying, harassment, hate speech, threat, toxic, offensive, and clean. Context-aware detection." },
    { icon: ShieldCheck, title: "Privacy First", desc: "All data processed securely. Role-based access control ensures only authorized team members see sensitive content." },
  ];

  const steps = [
    { num: "01", title: "Connect Your Platforms", desc: "Link your Facebook and Instagram pages with a single click. Our Meta API integration handles authentication and permissions." },
    { num: "02", title: "AI Scans Automatically", desc: "Every new comment, post, and message is analyzed by our multilingual AI models. No manual effort required." },
    { num: "03", title: "Review & Take Action", desc: "Dashboard shows all flagged content with severity scores. Moderate, delete, or ignore with one click." },
    { num: "04", title: "Track & Improve", desc: "Analytics reveal trends, repeat offenders, and platform health. Use data to make informed moderation decisions." },
  ];

  const faqs = [
    { q: "What platforms does CyberGuard support?", a: "CyberGuard currently supports Facebook Pages and Instagram business accounts through the Meta Graph API. We're actively working on Twitter/X, YouTube, and Discord integrations." },
    { q: "How accurate is the AI detection?", a: "Our models achieve 94-97% accuracy across supported languages. We use an ensemble of fine-tuned transformer models including DistilBERT and specialized multilingual classifiers." },
    { q: "Can I use it for multiple pages?", a: "Yes. CyberGuard supports multi-tenant architecture. Add multiple Facebook/Instagram pages, assign them to different workspaces, and manage everything from one dashboard." },
    { q: "Is my data secure?", a: "Absolutely. All data is encrypted in transit and at rest. Role-based access control ensures only authorized team members can view sensitive content. We never share your data with third parties." },
    { q: "What languages are supported?", a: "Our multilingual model supports 14+ languages including English, Arabic, Hindi, French, German, Spanish, Urdu, and more. Language is auto-detected and the best model is used." },
    { q: "How do I get started?", a: "Create an account, connect your Meta/Facebook pages via the Meta API setup guide, and the AI starts monitoring immediately. The entire setup takes about 10 minutes." },
  ];

  return (
    <div className={`landing-page ${dark ? "dark" : "light"}`}>
      {/* ── Navigation ──────────────────────────────────────── */}
      <nav className="landing-nav">
        <div className="landing-nav-inner">
          <a href="#" className="landing-logo">
            <div className="landing-logo-icon"><Shield size={22} strokeWidth={1.8} /></div>
            <span>CyberGuard</span>
          </a>
          <div className={`landing-nav-links ${mobileNavOpen ? "open" : ""}`}>
            <a href="#features" onClick={() => setMobileNavOpen(false)}>Features</a>
            <a href="#how-it-works" onClick={() => setMobileNavOpen(false)}>How It Works</a>
            <a href="#faq" onClick={() => setMobileNavOpen(false)}>FAQ</a>
          </div>
          <div className="landing-nav-actions">
            <button className="landing-theme-btn" onClick={toggleTheme} title={dark ? "Light mode" : "Dark mode"}>
              {dark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <button className="landing-login-btn" onClick={onLoginClick}>
              <LogIn size={16} /> Sign In
            </button>
            <button className="landing-hamburger" onClick={() => setMobileNavOpen(!mobileNavOpen)}>
              {mobileNavOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="landing-hero">
        <div className="landing-hero-glow" />
        <div className="landing-hero-content">
          <div className="landing-badge">
            <Sparkles size={14} /> AI-Powered Content Moderation
          </div>
          <h1 className="landing-hero-title">
            Protect Your Community<br />
            <span className="gradient-text">with Intelligent Detection</span>
          </h1>
          <p className="landing-hero-sub">
            CyberGuard uses advanced AI to automatically detect cyberbullying, harassment, and hate speech 
            across your social platforms. Real-time monitoring, actionable insights, and multi-language support.
          </p>
          <div className="landing-hero-actions">
            <button className="landing-cta-primary" onClick={onLoginClick}>
              Get Started Free <ArrowRight size={18} />
            </button>
            <a href="#features" className="landing-cta-secondary">
              Learn More
            </a>
          </div>
          <div className="landing-hero-stats">
            <div className="hero-stat">
              <span className="hero-stat-value">94%+</span>
              <span className="hero-stat-label">Detection Accuracy</span>
            </div>
            <div className="hero-stat">
              <span className="hero-stat-value">14+</span>
              <span className="hero-stat-label">Languages Supported</span>
            </div>
            <div className="hero-stat">
              <span className="hero-stat-value">Real-Time</span>
              <span className="hero-stat-label">Monitoring</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────── */}
      <section id="features" className="landing-section">
        <div className="landing-section-header">
          <h2>Everything you need for<br /><span className="gradient-text">safer communities</span></h2>
          <p>Built for moderators, community managers, and platform owners who take online safety seriously.</p>
        </div>
        <div className="features-grid">
          {features.map((f, i) => {
            const Icon = f.icon;
            return (
              <div key={i} className="feature-card">
                <div className="feature-icon-wrap"><Icon size={22} /></div>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── How It Works ─────────────────────────────────────── */}
      <section id="how-it-works" className="landing-section landing-section-alt">
        <div className="landing-section-header">
          <h2>Four simple steps to<br /><span className="gradient-text">safer communities</span></h2>
          <p>Get started in minutes, not days. No technical expertise required.</p>
        </div>
        <div className="steps-grid">
          {steps.map((s, i) => (
            <div key={i} className="step-card">
              <div className="step-number">{s.num}</div>
              <h3>{s.title}</h3>
              <p>{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Showcase ──────────────────────────────────────────── */}
      <section className="landing-section">
        <div className="landing-section-header">
          <h2>A glimpse of<br /><span className="gradient-text">what's inside</span></h2>
          <p>Beautifully designed dashboards that make moderation effortless.</p>
        </div>
        <div className="showcase-grid">
          <div className="showcase-card">
            <div className="showcase-card-header">
              <div className="showcase-dot" style={{ background: "#EF4444" }} />
              <div className="showcase-dot" style={{ background: "#EAB308" }} />
              <div className="showcase-dot" style={{ background: "#22C55E" }} />
            </div>
            <div className="showcase-card-body">
              <div className="showcase-chart">
                <div className="showcase-bar" style={{ height: "60%" }} />
                <div className="showcase-bar" style={{ height: "80%" }} />
                <div className="showcase-bar" style={{ height: "45%" }} />
                <div className="showcase-bar" style={{ height: "90%" }} />
                <div className="showcase-bar" style={{ height: "55%" }} />
                <div className="showcase-bar" style={{ height: "70%" }} />
              </div>
              <div className="showcase-legend">
                <span><span className="legend-dot" style={{ background: "#EF4444" }} /> Harassment</span>
                <span><span className="legend-dot" style={{ background: "#EAB308" }} /> Cyberbullying</span>
                <span><span className="legend-dot" style={{ background: "#22C55E" }} /> Clean</span>
              </div>
            </div>
          </div>
          <div className="showcase-stats">
            <div className="showcase-stat-item">
              <TrendingUp size={20} />
              <div>
                <span className="showcase-stat-val">1,247</span>
                <span className="showcase-stat-lbl">Comments Analyzed Today</span>
              </div>
            </div>
            <div className="showcase-stat-item">
              <AlertTriangle size={20} />
              <div>
                <span className="showcase-stat-val">38</span>
                <span className="showcase-stat-lbl">Flagged as Harmful</span>
              </div>
            </div>
            <div className="showcase-stat-item">
              <Zap size={20} />
              <div>
                <span className="showcase-stat-val">2.3s</span>
                <span className="showcase-stat-lbl">Average Response Time</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── FAQ ──────────────────────────────────────────────── */}
      <section id="faq" className="landing-section landing-section-alt">
        <div className="landing-section-header">
          <h2>Got questions?<br /><span className="gradient-text">We've got answers</span></h2>
        </div>
        <div className="faq-list">
          {faqs.map((faq, i) => (
            <div key={i} className={`faq-item ${openFaq === i ? "open" : ""}`}>
              <button className="faq-question" onClick={() => setOpenFaq(openFaq === i ? null : i)}>
                <span>{faq.q}</span>
                {openFaq === i ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
              </button>
              <div className="faq-answer">
                <p>{faq.a}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────── */}
      <section className="landing-cta-section">
        <div className="landing-cta-glow" />
        <div className="landing-cta-content">
          <h2>Ready to protect your community?</h2>
          <p>Join the waitlist for early access. No credit card required.</p>
          <button className="landing-cta-primary" onClick={onLoginClick}>
            Get Started Free <ArrowRight size={18} />
          </button>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────── */}
      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <div className="landing-footer-brand">
            <div className="landing-logo-icon"><Shield size={18} strokeWidth={1.8} /></div>
            <span>CyberGuard</span>
          </div>
          <div className="landing-footer-links">
            <a href="#">Privacy Policy</a>
            <a href="#">Terms of Service</a>
            <a href="mailto:hello@cyberguard.dev">Contact</a>
          </div>
          <p>&copy; 2026 CyberGuard. All rights reserved. Made with care for safer communities.</p>
        </div>
      </footer>
    </div>
  );
}
