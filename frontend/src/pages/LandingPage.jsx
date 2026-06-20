import { useState, useRef, useEffect } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { Shield, Sun, Moon, Menu, X, LogIn, AlertTriangle, BarChart3, Bell, Users, Radio, Layers, Globe, ChevronDown, ChevronRight, ArrowRight, Sparkles, ShieldCheck, Zap, TrendingUp, BookOpen, AppWindow, KeyRound, CheckCircle2, ExternalLink, Copy, FileText } from "lucide-react";

gsap.registerPlugin(ScrollTrigger);

export default function LandingPage({ onLoginClick }) {
  const [dark, setDark] = useState(() => localStorage.getItem("theme") !== "light");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [openFaq, setOpenFaq] = useState(null);
  const [guideTab, setGuideTab] = useState("meta");

  const heroRef = useRef(null);
  const heroBadgeRef = useRef(null);
  const heroTitleRef = useRef(null);
  const heroSubRef = useRef(null);
  const heroActionsRef = useRef(null);
  const heroStatsRef = useRef(null);
  const featuresRef = useRef(null);
  const stepsRef = useRef(null);
  const showcaseRef = useRef(null);
  const faqRef = useRef(null);
  const ctaRef = useRef(null);
  const guideRef = useRef(null);

  useEffect(() => {
    ScrollTrigger.refresh();
    const ctx = gsap.context(() => {
      const isDesktop = window.innerWidth > 768;

      if (isDesktop) {
        gsap.from(heroBadgeRef.current, { y: 30, opacity: 0, duration: 0.8, ease: "power3.out" });
        gsap.from(heroTitleRef.current, { y: 40, opacity: 0, duration: 0.8, ease: "power3.out", delay: 0.2 });
        gsap.from(heroSubRef.current, { y: 30, opacity: 0, duration: 0.8, ease: "power3.out", delay: 0.35 });
        gsap.from(heroActionsRef.current, { y: 30, opacity: 0, duration: 0.8, ease: "power3.out", delay: 0.5 });
        gsap.from(heroStatsRef.current, { y: 30, opacity: 0, duration: 0.8, ease: "power3.out", delay: 0.65 });
      } else {
        gsap.set(heroBadgeRef.current, { opacity: 1 });
        gsap.set(heroTitleRef.current, { opacity: 1 });
        gsap.set(heroSubRef.current, { opacity: 1 });
        gsap.set(heroActionsRef.current, { opacity: 1 });
        gsap.set(heroStatsRef.current, { opacity: 1 });
      }

      const setupScrollAnim = (container, opts = {}) => {
        if (!container?.children?.length) return;
        gsap.set(Array.from(container.children), { opacity: 0, y: opts.y || 40 });
        gsap.to(Array.from(container.children), {
          opacity: 1, y: 0, duration: opts.duration || 0.6,
          stagger: opts.stagger || 0.1, ease: "power3.out",
          scrollTrigger: {
            trigger: container, start: "top 85%",
            toggleActions: "play none none none",
            once: true,
          },
        });
      };

      setupScrollAnim(featuresRef.current, { stagger: 0.08 });
      setupScrollAnim(stepsRef.current, { stagger: 0.12 });

      if (showcaseRef.current?.children?.length) {
        gsap.set(Array.from(showcaseRef.current.children), { opacity: 0, y: 50 });
        gsap.to(Array.from(showcaseRef.current.children), {
          opacity: 1, y: 0, duration: 0.7, stagger: 0.12, ease: "power3.out",
          scrollTrigger: { trigger: showcaseRef.current, start: "top 85%", toggleActions: "play none none none", once: true },
        });
      }

      if (faqRef.current?.children?.length) {
        gsap.set(Array.from(faqRef.current.children), { opacity: 0, y: 30 });
        gsap.to(Array.from(faqRef.current.children), {
          opacity: 1, y: 0, duration: 0.5, stagger: 0.06, ease: "power3.out",
          scrollTrigger: { trigger: faqRef.current, start: "top 85%", toggleActions: "play none none none", once: true },
        });
      }

      if (guideRef.current) {
        gsap.set(guideRef.current, { opacity: 0, y: 40 });
        gsap.to(guideRef.current, {
          opacity: 1, y: 0, duration: 0.7, ease: "power3.out",
          scrollTrigger: { trigger: guideRef.current, start: "top 85%", toggleActions: "play none none none", once: true },
        });
      }

      if (ctaRef.current) {
        gsap.set(ctaRef.current, { opacity: 0, y: 40 });
        gsap.to(ctaRef.current, {
          opacity: 1, y: 0, duration: 0.8, ease: "power3.out",
          scrollTrigger: { trigger: ctaRef.current, start: "top 85%", toggleActions: "play none none none", once: true },
        });
      }
    });

    ScrollTrigger.refresh();
    return () => {
      ctx.revert();
      ScrollTrigger.getAll().forEach(st => st.kill());
    };
  }, []);

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
    { q: "What platforms does the app support?", a: "The app currently supports Facebook Pages and Instagram business accounts through the Meta Graph API. We're actively working on Twitter/X, YouTube, and Discord integrations." },
    { q: "How accurate is the AI detection?", a: "Our models achieve 94-97% accuracy across supported languages. We use an ensemble of fine-tuned transformer models including DistilBERT and specialized multilingual classifiers." },
    { q: "Can I use it for multiple pages?", a: "Yes. The app supports multi-tenant architecture. Add multiple Facebook/Instagram pages, assign them to different workspaces, and manage everything from one dashboard." },
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
            <span>AI-Powered Cyberbullying Detection</span>
          </a>
          <div className={`landing-nav-links ${mobileNavOpen ? "open" : ""}`}>
            <a href="#features" onClick={() => setMobileNavOpen(false)}>Features</a>
            <a href="#how-it-works" onClick={() => setMobileNavOpen(false)}>How It Works</a>
            <a href="#guide" onClick={() => setMobileNavOpen(false)}>Guide</a>
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
      <section className="landing-hero" ref={heroRef}>
        <div className="landing-hero-glow" />
        <div className="landing-hero-content">
          <div className="landing-badge" ref={heroBadgeRef}>
            <Sparkles size={14} /> AI-Powered Cyberbullying Detection
          </div>
          <h1 className="landing-hero-title" ref={heroTitleRef}>
            Protect Your Community<br />
            <span className="gradient-text">with Intelligent Detection</span>
          </h1>
          <p className="landing-hero-sub" ref={heroSubRef}>
            AI-Powered Cyberbullying Detection uses advanced AI to automatically detect cyberbullying, harassment, and hate speech 
            across your social platforms. Real-time monitoring, actionable insights, and multi-language support.
          </p>
          <div className="landing-hero-actions" ref={heroActionsRef}>
            <button className="landing-cta-primary" onClick={onLoginClick}>
              Get Started Free <ArrowRight size={18} />
            </button>
            <a href="#features" className="landing-cta-secondary">
              Learn More
            </a>
          </div>
          <div className="landing-hero-stats" ref={heroStatsRef}>
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
        <div className="features-grid" ref={featuresRef}>
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
        <div className="steps-grid" ref={stepsRef}>
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
        <div className="showcase-grid" ref={showcaseRef}>
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

      {/* ── Guide ──────────────────────────────────────────────── */}
      <section id="guide" className="landing-section landing-section-alt" ref={guideRef}>
        <div className="landing-section-header">
          <h2>Complete<br /><span className="gradient-text">Guide &amp; Setup</span></h2>
          <p>Everything you need to get the app up and running with your social platforms.</p>
        </div>

        <div className="guide-tabs">
          <button className={`guide-tab ${guideTab === "meta" ? "active" : ""}`} onClick={() => setGuideTab("meta")}>
            <KeyRound size={16} /> Meta API Setup
          </button>
          <button className={`guide-tab ${guideTab === "user" ? "active" : ""}`} onClick={() => setGuideTab("user")}>
            <FileText size={16} /> User Guide
          </button>
        </div>

        {guideTab === "meta" && (
          <div className="guide-content">
            <div className="guide-card">
              <div className="guide-card-header"><AppWindow size={18} /> Prerequisites</div>
              <ul className="guide-list">
                <li>Personal Facebook account</li>
                <li>A Facebook Page you own or manage</li>
                <li>Meta Developer Account (free)</li>
              </ul>
            </div>

            <div className="guide-card">
              <div className="guide-card-header"><AppWindow size={18} /> 1. Create a Meta Developer Account</div>
              <ol className="guide-list guide-list-num">
                <li>Go to <a href="https://developers.facebook.com" target="_blank" rel="noopener">developers.facebook.com</a></li>
                <li>Click <strong>"Get Started"</strong> and log in with your Facebook account</li>
                <li>Accept the terms and verify your email</li>
              </ol>
            </div>

            <div className="guide-card">
              <div className="guide-card-header"><AppWindow size={18} /> 2. Create a Meta App</div>
              <ol className="guide-list guide-list-num">
                <li>Go to <a href="https://developers.facebook.com/apps" target="_blank" rel="noopener">developers.facebook.com/apps</a></li>
                <li>Click <strong>"Create App"</strong> and select <strong>"Business"</strong> as the app type</li>
                <li>Name it <strong>AI-Powered Cyberbullying Detection</strong> and complete the security check</li>
              </ol>
            </div>

            <div className="guide-card">
              <div className="guide-card-header"><KeyRound size={18} /> 3. Get App ID &amp; App Secret</div>
              <ol className="guide-list guide-list-num">
                <li>Go to <strong>Settings &gt; Basic</strong> in your app dashboard</li>
                <li>Copy the <strong>App ID</strong> (visible immediately)</li>
                <li>Click <strong>"Show"</strong> to reveal the <strong>App Secret</strong> (enter your Facebook password)</li>
                <li>Enter both into the dashboard <strong>Settings &gt; Meta API</strong> page</li>
              </ol>
            </div>

            <div className="guide-card">
              <div className="guide-card-header"><KeyRound size={18} /> 4. Generate Access Tokens</div>
              <p className="guide-p">Create a System User in <strong>Business Settings &gt; Users &gt; System Users</strong>:</p>
              <ol className="guide-list guide-list-num">
                <li>Click <strong>"Add"</strong>, name it <code>cyberguard-system</code>, role: <strong>Admin</strong></li>
                <li>Add your Page as an asset with <strong>"Full Control"</strong></li>
                <li>Click <strong>"Generate New Token"</strong>, select your app</li>
                <li>Grant permissions: <code>pages_show_list</code>, <code>pages_read_engagement</code>, <code>pages_manage_posts</code>, <code>pages_manage_metadata</code>, <code>pages_read_user_content</code>, <code>pages_manage_engagement</code></li>
                <li>Click <strong>"Generate Token"</strong> and copy it immediately</li>
              </ol>
              <p className="guide-p">Paste this token into the dashboard <strong>Settings &gt; Meta API</strong> page.</p>
            </div>

            <div className="guide-card">
              <div className="guide-card-header"><ExternalLink size={18} /> 5. Get Your Page ID</div>
              <ol className="guide-list guide-list-num">
                <li>Go to your Facebook Page &gt; <strong>"About"</strong> &gt; scroll to <strong>"Page Transparency"</strong></li>
                <li>Copy the <strong>Page ID</strong> (a numeric value like <code>972933332575020</code>)</li>
                <li>Enter it into the dashboard <strong>Settings &gt; Meta API</strong> page</li>
              </ol>
            </div>

            <div className="guide-card">
              <div className="guide-card-header"><Radio size={18} /> 6. Set Up Webhooks — App Level</div>
              <p className="guide-p">Configure the webhook in your Meta App so it can receive events from Facebook:</p>
              <ol className="guide-list guide-list-num">
                <li>Go to <strong>Products &gt; Webhooks</strong> in your app dashboard</li>
                <li>Click <strong>"Add Subscription"</strong> next to <strong>Page</strong></li>
                <li><strong>Callback URL:</strong> <code>https://cyberguard-634541519354.asia-southeast1.run.app/api/webhook/meta</code></li>
                <li><strong>Verify Token:</strong> Any custom string (e.g. <code>my_verify_token</code>) — enter the same token in dashboard <strong>Settings &gt; Meta API</strong></li>
                <li>Click <strong>"Verify and Save"</strong> — you should see a green checkmark</li>
                <li>Under <strong>Subscription Fields</strong>, subscribe to: <code>feed</code></li>
                <li>Click <strong>"Save"</strong> on the field selection</li>
              </ol>
            </div>

            <div className="guide-card">
              <div className="guide-card-header"><Radio size={18} /> 7. Set Up Webhooks — Page Level</div>
              <p className="guide-p">The App-level webhook only tells Meta <em>"this app can receive events"</em>. You must also tell your Page <em>"send events to this app"</em>. Without this step, <strong>no real-time comments will arrive</strong>.</p>
              <p className="guide-p"><strong>Option A — Via App Dashboard (easiest):</strong></p>
              <ol className="guide-list guide-list-num">
                <li>Still in <strong>Products &gt; Webhooks</strong>, click the <strong>"Page"</strong> tab</li>
                <li>Scroll to <strong>"Page Subscriptions"</strong> section</li>
                <li>Find your page and click <strong>"Manage"</strong></li>
                <li>Confirm the fields include <code>feed</code></li>
              </ol>
              <p className="guide-p"><strong>Option B — Via API (curl):</strong></p>
              <div className="guide-code-block">
                <code>curl -X POST "https://graph.facebook.com/v25.0/YOUR_PAGE_ID/subscribed_apps" \<br />
                &nbsp;&nbsp;-d "subscribed_fields=feed" \<br />
                &nbsp;&nbsp;-d "access_token=YOUR_PAGE_ACCESS_TOKEN"</code>
              </div>
              <div className="guide-warning">
                <strong>⚠️ Both levels required.</strong><br />
                • <strong>App Level</strong> &mdash; tells Meta your app can handle webhooks<br />
                • <strong>Page Level</strong> &mdash; tells your page to send events to your app<br />
                If comments aren't appearing, the Page subscription is usually the missing piece.
              </div>
            </div>

            <div className="guide-card">
              <div className="guide-card-header"><CheckCircle2 size={18} /> 8. Test It</div>
              <p className="guide-p">Post a comment on your Facebook Page from a <strong>different Facebook account</strong> — admin self-comments are ignored by Meta. The comment should appear in your dashboard within seconds.</p>
            </div>
          </div>
        )}

        {guideTab === "user" && (
          <div className="guide-content">
            <div className="guide-card">
              <div className="guide-card-header"><BookOpen size={18} /> What Can the App Do?</div>
              <div className="guide-features-mini">
                <span><ShieldCheck size={14} /> Analyze Text</span>
                <span><Radio size={14} /> Live Monitoring</span>
                <span><BarChart3 size={14} /> Dashboard</span>
                <span><FileText size={14} /> History</span>
              </div>
            </div>

            <div className="guide-card">
              <div className="guide-card-header"><BarChart3 size={18} /> Dashboard</div>
              <p className="guide-p">The home page shows <strong>Total Flagged</strong>, <strong>Critical Threats</strong>, severity distribution, and a bar chart of content by category. Click <strong>Refresh</strong> to update charts.</p>
            </div>

            <div className="guide-card">
              <div className="guide-card-header"><ShieldCheck size={18} /> Analyze Text</div>
              <ol className="guide-list guide-list-num">
                <li>Click <strong>Analyze</strong> in the sidebar</li>
                <li>Type or paste any text into the input box</li>
                <li>Click <strong>Analyze →</strong></li>
                <li>Result shows: category (cyberbullying, harassment, hate speech, threat, or clean), confidence percentage, and probability bars</li>
              </ol>
            </div>

            <div className="guide-card">
              <div className="guide-card-header"><FileText size={18} /> History</div>
              <p className="guide-p">Shows all flagged content. Filter by category using the top buttons. Navigate pages with <strong>Prev / Next</strong>.</p>
            </div>

            <div className="guide-card">
              <div className="guide-card-header"><Radio size={18} /> Live Feed / Simulate</div>
              <p className="guide-p">Test the system with sample social media comments. Add your own test comments, select Instagram or Facebook as the platform, and see real-time analysis.</p>
            </div>

            <div className="guide-card">
              <div className="guide-card-header"><AlertTriangle size={18} /> Understanding Results</div>
              <div className="guide-table-wrap">
                <table className="guide-table">
                  <thead><tr><th>Category</th><th>Severity</th><th>Action</th></tr></thead>
                  <tbody>
                    <tr><td>Clean</td><td>None</td><td>Content is safe</td></tr>
                    <tr><td>Cyberbullying</td><td>Low–Medium</td><td>Review recommended</td></tr>
                    <tr><td>Harassment</td><td>Medium–High</td><td>Prompt review needed</td></tr>
                    <tr><td>Hate Speech</td><td>High</td><td>Review and consider action</td></tr>
                    <tr><td>Threat</td><td>Critical</td><td>Immediate action required</td></tr>
                  </tbody>
                </table>
              </div>
              <p className="guide-p" style={{ marginTop: 12 }}>Confidence scores above <strong>80%</strong> are reliable. Scores 50–70% should be reviewed manually.</p>
            </div>

            <div className="guide-card">
              <div className="guide-card-header"><Globe size={18} /> Connecting Facebook / Instagram</div>
              <p className="guide-p">Follow the <strong>Meta API Setup</strong> tab above. The app must pass Meta's App Review process for production use. Once configured, new comments are automatically analyzed and appear in the Dashboard and History.</p>
            </div>

            <div className="guide-card">
              <div className="guide-card-header"><Zap size={18} /> Limitations</div>
              <ul className="guide-list">
                <li>AI is not 100% accurate — always use human judgment</li>
                <li>Sarcasm and context-dependent language can confuse the model</li>
                <li>Best with English text (multilingual support: 14+ languages)</li>
                <li>History is cleared on server restart unless database persistence is enabled</li>
              </ul>
            </div>
          </div>
        )}
      </section>

      {/* ── FAQ ──────────────────────────────────────────────── */}
      <section id="faq" className="landing-section landing-section-alt">
        <div className="landing-section-header">
          <h2>Got questions?<br /><span className="gradient-text">We've got answers</span></h2>
        </div>
        <div className="faq-list" ref={faqRef}>
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
      <section className="landing-cta-section" ref={ctaRef}>
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
<span>AI-Powered Cyberbullying Detection</span>
          </div>
          <div className="landing-footer-links">
            <a href="#features">Features</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#faq">FAQ</a>
            <a href="mailto:hello@aicyberbullying.dev">Contact</a>
          </div>
          <p>&copy; 2026 AI-Powered Cyberbullying Detection. All rights reserved. Made with care for safer communities.</p>
        </div>
      </footer>
    </div>
  );
}
