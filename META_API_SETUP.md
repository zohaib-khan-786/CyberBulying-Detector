# Meta API Integration — Complete Setup Guide

This guide covers everything needed to connect your Facebook Page to the AI-Powered Cyberbullying Detection app for real-time comment monitoring.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Create a Meta Developer Account](#2-create-a-meta-developer-account)
3. [Create a Meta App](#3-create-a-meta-app)
4. [Get App ID & App Secret](#4-get-app-id--app-secret)
5. [Generate Page Access Token](#5-generate-page-access-token)
6. [Get Your Page ID](#6-get-your-page-id)
7. [Configure Meta Credentials in the App](#7-configure-meta-credentials-in-the-app)
8. [Set Up Webhooks — App Level](#8-set-up-webhooks--app-level)
9. [Set Up Webhooks — Page Level](#9-set-up-webhooks--page-level)
10. [Required Permissions](#10-required-permissions)
11. [Testing](#11-testing)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Prerequisites

- A personal Facebook account
- A Facebook Page you own or manage
- A Meta Developer Account (free)

---

## 2. Create a Meta Developer Account

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Click **"Get Started"** and log in with your Facebook account
3. Accept the terms and verify your email

---

## 3. Create a Meta App

1. Go to [developers.facebook.com/apps](https://developers.facebook.com/apps)
2. Click **"Create App"**
3. Select **"Business"** as the app type
4. Name it **AI-Powered Cyberbullying Detection**
5. Complete the security check

### Add Products

In your app dashboard, add the following products:

- **Webhooks** — for receiving real-time events
- **Instagram Basic Display** (optional, for Instagram comments)

---

## 4. Get App ID & App Secret

1. Go to **Settings > Basic** in your app dashboard
2. Copy the **App ID** (visible immediately)
3. Click **"Show"** to reveal the **App Secret** (enter your Facebook password)

---

## 5. Generate Page Access Token

Create a **System User** for long-lived token access:

1. Go to **Business Settings > Users > System Users**
   - URL: `https://business.facebook.com/settings/system-users`
2. Click **"Add"**
3. Name: `cyberguard-system`, Role: **Admin**
4. Click **"Add Asset"** → select your Facebook Page → **"Full Control"**
5. Click **"Generate New Token"** → select your app
6. Grant these permissions:

| Permission | Purpose |
|-----------|---------|
| `pages_show_list` | List pages you manage |
| `pages_read_engagement` | Read comments and reactions |
| `pages_manage_posts` | Create/delete posts |
| `pages_manage_metadata` | Update webhook settings |
| `pages_read_user_content` | Read user content on page |
| `pages_manage_engagement` | Reply to comments |
| `business_management` | Access Business settings |

7. Click **"Generate Token"** and copy it immediately (it won't be shown again)

> **Note:** This token does not expire unless revoked. Save it securely.

---

## 6. Get Your Page ID

1. Go to your Facebook Page
2. Click **"About"** (left sidebar)
3. Scroll to **"Page Transparency"** section
4. Copy the **Page ID** (a numeric value like `972933332575020`)

---

## 7. Configure Meta Credentials in the App

Log in to the dashboard and go to **Settings > Meta API**, then enter:

| Field | Value |
|-------|-------|
| **App ID** | From Step 4 |
| **App Secret** | From Step 4 |
| **Page ID** | From Step 6 |
| **Page Access Token** | From Step 5 |
| **Webhook Verify Token** | Any custom string (e.g., `my_verify_token`) |

Click **"Save Configuration"**. Then click **"Test Configuration"** — all tests should pass:
- ✅ Token Validity
- ✅ Permissions
- ✅ Page Access
- ✅ Direct Page Access
- ✅ Page Feed Access

---

## 8. Set Up Webhooks — App Level

This tells Meta that your app can receive webhook events.

1. In your app dashboard, go to **Products > Webhooks**
2. Click **"Add Subscription"** next to **Page**
3. Fill in:

| Field | Value |
|-------|-------|
| **Callback URL** | `https://your-app-url.com/api/webhook/meta` |
| **Verify Token** | Same string you entered in Step 7 |

For Cloud Run deployment:
```
Callback URL: https://cyberguard-634541519354.asia-southeast1.run.app/api/webhook/meta
```

For local development (via ngrok):
```
Callback URL: https://your-ngrok-url.ngrok-free.app/api/webhook/meta
```

4. Click **"Verify and Save"** — you should see a green checkmark
5. Under **"Subscription Fields"**, select: `feed`
6. Click **"Save"**

---

## 9. Set Up Webhooks — Page Level

This tells your Facebook Page to send events to your app. **Both levels are required.**

### Option A — Via App Dashboard

1. Still in **Products > Webhooks**, click the **"Page"** tab
2. Scroll to **"Page Subscriptions"** section
3. Find your page and click **"Manage"**
4. Confirm the fields include `feed`

### Option B — Via API (curl)

```bash
curl -X POST "https://graph.facebook.com/v25.0/YOUR_PAGE_ID/subscribed_apps" \
  -d "subscribed_fields=feed" \
  -d "access_token=YOUR_PAGE_ACCESS_TOKEN"
```

**Expected response:**
```json
{"success": true}
```

To verify:
```bash
curl "https://graph.facebook.com/v25.0/YOUR_PAGE_ID/subscribed_apps?access_token=YOUR_PAGE_ACCESS_TOKEN"
```

**Expected response:**
```json
{"data":[{"subscribed_fields":["feed"],"id":"YOUR_APP_ID","name":"Your App Name"}]}
```

---

## 10. Required Permissions Summary

| # | Permission | Where to Grant |
|---|-----------|----------------|
| 1 | `pages_show_list` | System User Token Generation |
| 2 | `pages_read_engagement` | System User Token Generation |
| 3 | `pages_manage_posts` | System User Token Generation |
| 4 | `pages_manage_metadata` | System User Token Generation |
| 5 | `pages_read_user_content` | System User Token Generation |
| 6 | `pages_manage_engagement` | System User Token Generation |
| 7 | `business_management` | System User Token Generation |
| 8 | App ID + App Secret | Settings > Basic |
| 9 | Webhook: `feed` field | Products > Webhooks |
| 10 | Page subscription | Graph API `/subscribed_apps` |

---

## 11. Testing

### A. Configuration Test

In dashboard **Settings > Meta API**, click **"Test Configuration"**:

| Test | Expected |
|------|----------|
| Token Validity | ✅ PASS |
| Permissions | ✅ PASS (all 7 permissions) |
| Page Access | ✅ PASS (1 page accessible) |
| Direct Page Access | ✅ PASS |
| Page Feed Access | ✅ PASS |

### B. Live Comment Test

1. Open your Facebook Page in a **different browser** (not logged in as admin — Meta ignores self-comments)
2. Post a comment on any page post
3. Within seconds, it should appear in the dashboard **Dashboard > Recent Flags** or **Moderation > Facebook Comments**

### C. Webhook Verification

Meta sends a test ping when you configure the webhook. To manually verify:

```bash
# Check webhook endpoint
curl https://your-app-url.com/api/webhook/test

# Expected:
{"message":"Webhook route is working","status":"ok","verify_token":"your_token"}
```

---

## 12. Troubleshooting

### Issue: Page Feed Access shows FAIL

**Cause:** Using a User Token instead of a Page Access Token.

**Fix:** Ensure you generated the token through **System Users** (Step 5), not through the Graph API Explorer.

---

### Issue: Webhook verification fails

**Cause:** Callback URL or Verify Token mismatch.

**Fix:**
1. Confirm the Callback URL is exactly `https://your-app.com/api/webhook/meta`
2. The Verify Token in Meta Developer Portal matches what's in the app Settings page
3. The app is running and accessible from the internet

---

### Issue: Comments not appearing in real-time

**Cause 1:** Page-level subscription missing.

**Fix:** Run the `/subscribed_apps` API call (Step 9).

```bash
curl -X POST "https://graph.facebook.com/v25.0/YOUR_PAGE_ID/subscribed_apps" \
  -d "subscribed_fields=feed" \
  -d "access_token=YOUR_PAGE_ACCESS_TOKEN"
```

**Cause 2:** You're commenting as the page admin.

**Fix:** Use a different Facebook account to post comments.

---

### Issue: Token expired

**Cause:** Using a short-lived token.

**Fix:** Generate a **long-lived** token via System User (Step 5). System User tokens do not expire.

---

### Issue: 502 Bad Gateway on Cloud Run

**Cause:** The backend (gunicorn) isn't running yet.

**Fix:** The model loads in the background on startup. Wait 10–30 seconds. If it persists, check Cloud Run logs:
```
gcloud logs read --project=your-project-id
```

---

### Issue: Webhook signature verification failed

**Cause:** App Secret mismatch.

**Fix:** Ensure the App Secret in dashboard **Settings > Meta API** matches exactly what's in **Settings > Basic** in the Meta Developer Portal.
