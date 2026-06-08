# CyberGuard — User Guide

Welcome to **CyberGuard**, an AI-powered tool that automatically detects cyberbullying, harassment, hate speech, and threats in text — including live comments from Facebook and Instagram.

---

## What Can CyberGuard Do?

| Feature | Description |
|---------|-------------|
| **Analyze Text** | Paste any comment or message and get an instant safety rating |
| **Live Monitoring** | Connect to your Facebook Page or Instagram account to flag harmful comments in real time |
| **Dashboard** | See a live overview of flagged content, categories, and severity levels |
| **History** | Browse all previously flagged content, filter by type |
| **Simulate** | Test the system with sample comments before connecting real social media accounts |

---

## Getting Started

### First Time Setup

1. Make sure the app is running (your developer will handle this — see the Developer README)
2. Open your browser and go to **http://localhost:3000**
3. You will see the **Dashboard** page

No account or login is required for the local version.

---

## Pages Guide

### Dashboard

The home page. Shows:

- **Total Flagged** — how many harmful messages have been detected in this session
- **Critical Threats** — count of messages flagged as most severe
- **High Severity** — serious harmful content
- **Accuracy** — the model's accuracy rating on test data
- **Content by Category** — bar chart showing cyberbullying vs harassment vs hate speech vs threats
- **Severity Distribution** — breakdown from low to critical
- **Recent Flags** — the latest flagged messages

Click **↻ Refresh** to update the charts with the latest data.

---

### Analyze Text

Use this to check any single piece of text.

1. Click **Analyze Text** in the left sidebar
2. Type or paste any comment, message, or post into the text box
3. Click **Analyze →**
4. The result appears below:
   - **Green ✓** = content appears safe
   - **Orange / Red ⚠** = harmful content detected
   - The **category** tells you what type (cyberbullying, harassment, etc.)
   - The **confidence** percentage shows how certain the AI is
   - The **probability bars** show scores across all categories

**Example inputs to try:**
- `"You are so stupid, nobody likes you"` → should flag as cyberbullying
- `"Have a great day!"` → should pass as clean
- `"I will find you and make you pay"` → should flag as threat

---

### History

Shows all flagged content from the current session.

- Use the **filter buttons** at the top to show only a specific category
- Each row shows severity icon, category, a preview of the text, confidence, and source
- Use **Prev / Next** to navigate pages

> Note: History is cleared when the server restarts. For permanent storage, ask your developer to enable database persistence.

---

### Simulate Social Feed

This page lets you test the system as if real social media comments were coming in — without needing a real Meta API connection.

**How to use:**
1. Click **Simulate Social Feed** in the sidebar
2. You will see a list of sample comments from Instagram/Facebook
3. Click **Analyze** on any individual comment, or press **Run All ▶** to analyze all at once
4. Cards turn **red** for harmful content, **green** for safe content

**Add your own test comment:**
1. Type your comment in the input box at the top
2. Select **Instagram** or **Facebook** as the platform
3. Click **Simulate** (or press Enter)
4. The comment will be added to the list and analyzed immediately

---

## Understanding the Results

### Categories

| Category | What it means |
|----------|--------------|
| **Clean** | No harmful content detected |
| **Cyberbullying** | Personal attacks, name-calling, insults targeted at a person |
| **Harassment** | Persistent threatening or intimidating behaviour |
| **Hate Speech** | Content targeting a group based on identity |
| **Threat** | Direct threats of physical harm |

### Severity Levels

| Icon | Level | Action |
|------|-------|--------|
| 🟢 | None | Content is safe |
| 🟡 | Low | Mildly concerning, worth noting |
| 🟠 | Medium | Clearly harmful, review recommended |
| 🔴 | High | Serious, prompt review needed |
| 🚨 | Critical | Immediate action required |

### Confidence Score

The percentage shown (e.g. **89.2%**) is how confident the AI is in its classification. Scores above 80% are generally reliable. Scores between 50–70% should be reviewed manually.

---

## Connecting to Facebook / Instagram (Advanced)

To monitor your real social media accounts:

1. Ask your developer to complete the **Meta API setup** (App Review required — takes 1–2 weeks)
2. Once approved, your developer will configure the webhook URL to point at this server
3. New comments on your Facebook Page or Instagram Business account will automatically be analyzed and appear in the Dashboard and History pages

> This feature requires a **Facebook Business account** and your app passing Meta's App Review process.

---

## Limitations

- The AI is not 100% accurate. Always use human judgment for serious cases.
- Sarcasm, irony, and context-dependent language can confuse the model.
- The system currently works best with **English** text. Multilingual support is on the roadmap.
- History is **not saved** between server restarts unless database persistence is enabled.

---

## Frequently Asked Questions

**Q: Can I use this for WhatsApp messages?**
No, WhatsApp does not allow third-party content monitoring due to end-to-end encryption.

**Q: What happens to the text I analyze?**
Text is processed locally on your server and stored only in memory (lost on restart). Nothing is sent to external services unless you have the HuggingFace transformer enabled.

**Q: How do I improve accuracy for my use case?**
Ask your developer to retrain the model on a dataset that matches your platform's language and content.

**Q: The result seems wrong. What should I do?**
AI classifiers make mistakes, especially with sarcasm or cultural context. Always verify serious cases manually. You can use the **confidence score** as a guide — low confidence means the result is less certain.

---

## Need Help?

Contact your developer or system administrator. For developer setup instructions, see the **README.md** in the project root.
