# CyberGuard — Meta API Complete Setup Guide

This guide walks you through every step of connecting CyberGuard to Facebook/Instagram for live comment monitoring. Follow each section in order.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Create a Meta Developer Account](#2-create-a-meta-developer-account)
3. [Create a Meta App](#3-create-a-meta-app)
4. [Get App ID and App Secret](#4-get-app-id-and-app-secret)
5. [Generate Access Tokens](#5-generate-access-tokens)
6. [Grant Required Permissions](#6-grant-required-permissions)
7. [Get Your Page ID](#7-get-your-page-id)
8. [Set Up Webhooks](#8-set-up-webhooks)
9. [Subscribe Your Page to the App](#9-subscribe-your-page-to-the-app)
10. [Configure the .env File](#10-configure-the-env-file)
11. [Set Up ngrok (Local Development)](#11-set-up-ngrok-local-development)
12. [Test Everything](#12-test-everything)
13. [Troubleshooting](#13-troubleshooting)
14. [Meta API Quirks and Known Issues](#14-meta-api-quirks-and-known-issues)

---

## 1. Prerequisites

Before you start, make sure you have:

- A **personal Facebook account** (not a business account — personal accounts can create apps)
- A **Facebook Page** that you own or manage (this is where comments will be monitored)
- A **Meta Developer Account** (free — you'll create this in step 2)
- **Node.js** installed (for running the app locally)
- **Python 3.10** installed (for the Flask backend)
- **ngrok** installed (for local webhook testing — free tier works)

---

## 2. Create a Meta Developer Account

If you already have a developer account, skip to step 3.

1. Go to **https://developers.facebook.com**
2. Click **"Get Started"** in the top right
3. Log in with your personal Facebook account
4. Accept the terms and conditions
5. Verify your email address
6. You're now a Meta Developer — you can create apps

---

## 3. Create a Meta App

1. Go to **https://developers.facebook.com/apps**
2. Click **"Create App"** (green button, top right)
3. Select **"Business"** as the app type (this gives you access to Pages and Webhooks)
4. Click **"Next"**
5. Fill in:
   - **App Name:** `CyberGuard` (or any name you prefer)
   - **App Contact Email:** your email address
6. Click **"Create App"**
7. Complete the security check (enter your Facebook password)

You'll be taken to the app dashboard.

---

## 4. Get App ID and App Secret

These are needed for the `.env` file.

1. In your app dashboard, go to **Settings > Basic**
2. You'll see:
   - **App ID** — visible immediately (e.g., `1537368314572984`)
   - **App Secret** — click **"Show"** and enter your Facebook password to reveal it
3. Copy both values — you'll need them for the `.env` file

**Important:** Never share your App Secret publicly. It's like a password for your app.

---

## 5. Generate Access Tokens

Meta uses a token system. You'll generate a short-lived token, exchange it for a long-lived token, then get a Page Access Token.

### Step 5.1: Create a System User (Required)

System users are needed to generate long-lived tokens that don't expire.

1. Go to **Business Manager > Business Settings** (https://business.facebook.com/settings)
   - If you don't have a Business Manager account, create one at https://business.facebook.com
2. In the left sidebar, go to **Users > System Users**
3. Click **"Add"**
4. Name: `cyberguard-system` (or any name)
5. Role: **Admin**
6. Click **"Create System User"**
7. **Add Assets:**
   - Click **"Add Assets"** next to the system user
   - Select **"Pages"**
   - Select your page ("ZK Lab" or whatever it's called)
   - Give it **"Full Control"** (all permissions)
   - Click **"Save Changes"**

### Step 5.2: Generate a System User Token

1. Still in Business Settings > System Users, click on your system user
2. Click **"Generate New Token"**
3. Select your app from the dropdown
4. Check these permissions:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
   - `pages_manage_metadata`
   - `pages_read_user_content`
   - `pages_manage_engagement`
   - `instagram_basic`
   - `instagram_manage_comments`
   - `instagram_manage_messages`
5. Click **"Generate Token"**
6. **Copy this token immediately** — it won't be shown again

This is your **long-lived Page Access Token**. It doesn't expire as long as you don't revoke it.

### Step 5.3: Alternative — User Token Exchange (Simpler but expires)

If you don't want to set up Business Manager, you can use this flow:

1. Go to **Graph API Explorer** (https://developers.facebook.com/tools/explorer/)
2. In the top right, select your app from the dropdown
3. Click **"Generate Access Token"**
4. Log in with your Facebook account
5. Grant the permissions listed in Step 5.2
6. Copy the **Short-lived User Access Token**
7. Go to **https://graph.facebook.com/v25.0/oauth/access_token** and exchange it:

```
GET https://graph.facebook.com/v25.0/oauth/access_token?
  grant_type=fb_exchange_token&
  client_id={YOUR_APP_ID}&
  client_secret={YOUR_APP_SECRET}&
  fb_exchange_token={SHORT_LIVED_TOKEN}
```

This gives you a **Long-lived User Access Token** (60 days).

8. Then get a **Page Access Token**:

```
GET https://graph.facebook.com/v25.0/me/accounts?
  access_token={LONG_LIVED_USER_TOKEN}
```

**Note:** If `/me/accounts` returns empty data (a known issue), you'll need to use the System User method from Step 5.1, or manually set `META_PAGE_ID` in your `.env` file and use the token from Step 5.2.

---

## 6. Grant Required Permissions

Your app needs these permissions approved by Meta before it can access Page data:

### In the App Dashboard:

1. Go to **App Review > Permissions and Features**
2. Search for and request these permissions:

| Permission | What It Does | Required? |
|------------|--------------|-----------|
| `pages_show_list` | See the list of Pages you manage | Yes |
| `pages_read_engagement` | Read comments, reactions, and posts on Pages | Yes |
| `pages_manage_posts` | Create, edit, delete posts on Pages | For moderation (delete) |
| `pages_manage_metadata` | Access Page metadata and webhooks | Yes |
| `pages_read_user_content` | Read user-generated content on Pages | Yes |
| `pages_manage_engagement` | Manage comments and reactions | For moderation (warn) |
| `instagram_basic` | Access Instagram Business account data | If using Instagram |
| `instagram_manage_comments` | Read and manage Instagram comments | If using Instagram |
| `instagram_manage_messages` | Read and manage Instagram messages | If using Instagram |

### For Development Mode (Testing):

- You can test with all permissions granted without App Review
- Only **app admins, developers, and testers** can trigger webhook events
- Add test users in **App Dashboard > Roles > Roles**

### For Live Mode (Production):

- Submit your app for **App Review** (takes 1-2 weeks)
- Meta will review your app and approve the permissions
- Once approved, webhook events work for all users

---

## 7. Get Your Page ID

Every Facebook Page has a unique numeric ID.

### Method 1: From Page Info

1. Go to your Facebook Page
2. Click **"About"** in the left sidebar
3. Scroll down to **"Page Transparency"**
4. You'll see **"Page ID"** — copy the number

### Method 2: From Graph API Explorer

1. Go to **https://developers.facebook.com/tools/explorer/**
2. Select your app
3. Enter `me` in the query box
4. Click **"Submit"**
5. Find `id` in the response — that's your User ID, not Page ID

To get Page ID:
1. Enter `me/accounts` in the query box
2. Click **"Submit"**
3. Find your page in the `data` array
4. Copy the `id` field

### Method 3: From Page URL

Go to your Page, right-click > "View Page Source", search for `"pageID"` — you'll find the numeric ID.

**Example:** Your Page ID might look like `972933332575020`

---

## 8. Set Up Webhooks

Webhooks let Meta send comment events to your server in real-time.

### Step 8.1: Set Up ngrok (Local Development)

Meta requires a publicly accessible HTTPS URL. For local development, use ngrok:

1. Open a terminal
2. Run:
   ```bash
   ngrok http 5000
   ```
3. You'll see a URL like:
   ```
   https://sylas-unnarrow-guillermina.ngrok-free.dev
   ```
4. **Keep this terminal open** — the URL changes when you restart ngrok (unless you have a paid plan)

### Step 8.2: Configure Webhook in Meta Dashboard

1. In your app dashboard, go to **Products > Webhooks**
2. You'll see a configuration section with:
   - **Callback URL:** Enter your ngrok URL + `/api/webhook/meta`
     - Example: `https://sylas-unnarrow-guillermina.ngrok-free.dev/api/webhook/meta`
   - **Verify Token:** Enter the same value as `META_WEBHOOK_VERIFY_TOKEN` in your `.env` file
     - Example: `any_custom_string_you_choose`
3. Click **"Verify and Save"**
4. Meta will send a GET request to verify the URL — it should show a green **"Verified"** checkmark

### Step 8.3: Subscribe to Webhook Fields

1. In the Webhooks page, you'll see a list of webhook fields
2. Find and **subscribe** to these fields:

| Field | What It Does |
|-------|--------------|
| `feed` | Facebook post comments, reactions, shares |
| `messages` | Direct messages to your Page |
| `message_deliveries` | Message delivery confirmations |
| `message_echoes` | Message echo events |
| `name` | Page name changes |
| `page_upcoming_change` | Scheduled Page changes |
| `business_integrity` | Content policy violations |
| `group_feed` | Group post events (if applicable) |

3. Click **"Subscribe"** next to each field

**Important:** The `feed` field is the critical one — it sends events when someone comments on your Page's posts.

### Step 8.4: Subscribe Your Page (CRITICAL — Often Missed)

This is the step that catches most people. Even with the webhook configured and fields subscribed, **Meta won't send events unless your Page is explicitly subscribed to your app**.

#### Method 1: Via Graph API (Recommended)

Run this command (replace the values):

```bash
curl -X POST "https://graph.facebook.com/v25.0/{YOUR_PAGE_ID}/subscribed_apps" \
  -d "subscribed_fields=feed,messages" \
  -d "access_token={YOUR_PAGE_ACCESS_TOKEN}"
```

Or in Python:

```python
import requests

PAGE_ID = "your_page_id"
PAGE_ACCESS_TOKEN = "your_page_access_token"

url = f"https://graph.facebook.com/v25.0/{PAGE_ID}/subscribed_apps"
data = {
    "subscribed_fields": "feed,messages",
    "access_token": PAGE_ACCESS_TOKEN
}
response = requests.post(url, data=data)
print(response.json())  # Should show {"success": true}
```

#### Method 2: Via Business Manager

1. Go to **Business Manager > Business Settings**
2. Go to **Accounts > Pages**
3. Select your Page
4. Under **"Apps"**, click **"Add"**
5. Select your CyberGuard app
6. Click **"Add"**

### Step 8.5: Verify Page Subscription

After subscribing, verify it worked:

```bash
curl "https://graph.facebook.com/v25.0/{YOUR_PAGE_ID}/subscribed_apps?access_token={YOUR_PAGE_ACCESS_TOKEN}"
```

You should see:

```json
{
  "data": [
    {
      "name": "CyberGuard",
      "id": "your_app_id",
      "subscribed_fields": ["feed", "messages"]
    }
  ]
}
```

If `"data": []` — the subscription failed. Check your Page Access Token permissions.

---

## 9. Subscribe Your Page to the App

(This is a duplicate of Step 8.4 — included here for clarity)

**This is the most commonly missed step.** Without it, webhook events will never arrive.

Run:

```python
import requests

url = f"https://graph.facebook.com/v25.0/{PAGE_ID}/subscribed_apps"
data = {
    "subscribed_fields": "feed,messages",
    "access_token": PAGE_ACCESS_TOKEN
}
response = requests.post(url, data=data)
print(response.json())  # {"success": true}
```

---

## 10. Configure the .env File

Open the `.env` file in the project root and fill in your values:

```bash
# ── Meta (Facebook / Instagram) ───────────────────────────────────────────
META_APP_ID=your_app_id_here                    # From Step 4
META_APP_SECRET=your_app_secret_here            # From Step 4 (keep secret!)
META_PAGE_ID=your_page_id_here                  # From Step 7
META_PAGE_ACCESS_TOKEN=your_page_access_token   # From Step 5
META_WEBHOOK_VERIFY_TOKEN=any_custom_string     # From Step 8.2
```

**Example with real values:**

```bash
META_APP_ID=1537368314572984
META_APP_SECRET=612bc6773ea6c95f0f974638f2c93e86
META_PAGE_ID=972933332575020
META_PAGE_ACCESS_TOKEN=EAAV2OnRHcLgBRcQiSsDNy3aJNvgZB0UrZALQBLpinnRKn6Dkwsfo0tilxV2SGWRn95EV1iHcsN6brzyLZBvgrZCMCZAnF1mg0ZC2886hIP6lFKq6c5yaNLyNVDDzGV9ZBZByyWHuLE2aquh6C9i8HQZAVqr22eEuzS3XfGaZAS6656eu8odWY5zNJWIeY6OXiOh2X9Yr8bctBXhE8zLZB9JH829stFCDpauZAU0Skk3A0DgZD
META_WEBHOOK_VERIFY_TOKEN=any_custom_string_you_choose
```

**Important Notes:**
- `META_APP_SECRET` must be set for webhook signature verification to work
- `META_PAGE_ID` is required because `/me/accounts` may return empty data
- `META_PAGE_ACCESS_TOKEN` should be a long-lived token (not short-lived)
- Never commit the `.env` file to git — it contains secrets

---

## 11. Set Up ngrok (Local Development)

### Install ngrok

1. Go to **https://ngrok.com**
2. Sign up for a free account
3. Download ngrok for Windows
4. Extract and add to your PATH

### Start ngrok

1. Open a terminal
2. Run:
   ```bash
   ngrok http 5000
   ```
3. Copy the **HTTPS URL** (e.g., `https://sylas-unnarrow-guillermina.ngrok-free.dev`)
4. Update the webhook URL in Meta Dashboard if ngrok gives you a new URL

### Keep ngrok Running

- ngrok must be running while you test webhooks
- The free tier gives you a new URL each time you restart
- If the URL changes, update it in the Meta Dashboard

---

## 12. Test Everything

### Step 12.1: Test Webhook Verification

```bash
curl "https://your-ngrok-url/api/webhook/meta?hub.mode=subscribe&hub.verify_token=any_custom_string_you_choose&hub.challenge=TEST123"
```

Expected response: `TEST123`

### Step 12.2: Test Manual Comment Fetch

1. Open the app at **http://localhost:3000**
2. Go to **Meta API Test** page
3. Click **"Test Connection"** — should show your Page info
4. Click **"Fetch Comments"** — should pull recent comments

### Step 12.3: Test Webhook Events

1. Make sure ngrok is running
2. Make sure the Flask backend is running
3. Go to your Facebook Page in a **different browser** (or use a different Facebook account)
4. Find a post on your Page
5. Leave a comment on that post
6. Watch the Flask backend terminal — you should see:
   ```
   WEBHOOK RECEIVED — 200 OK  (0.XXs)
   ```
7. Go to **Live Feed** in the app — the comment should appear (auto-refreshes every 5 seconds)

### Step 12.4: Test from a Different Account

**Important:** Meta ignores webhook events when the page admin comments on their own posts. Always test from a different Facebook account.

1. Log out of Facebook
2. Log in with a different account (or ask a friend)
3. Comment on your Page's post
4. The comment should appear in the Live Feed

---

## 13. Troubleshooting

### Webhook Not Receiving Events

1. **Check ngrok is running:**
   ```bash
   curl http://localhost:4040/api/requests/http?limit=5
   ```

2. **Check page subscription:**
   ```bash
   curl "https://graph.facebook.com/v25.0/{PAGE_ID}/subscribed_apps?access_token={TOKEN}"
   ```
   Should show your app with `subscribed_fields: ["feed", "messages"]`

3. **Check webhook verification:**
   - In Meta Dashboard > Webhooks, you should see a green **"Verified"** checkmark

4. **Check app mode:**
   - Development mode: Only admins/developers/testers receive events
   - Live mode: All users receive events

5. **Check you're not self-commenting:**
   - Admin comments on own Page posts are ignored by Meta

### `/me/accounts` Returns Empty

This is a known Meta API issue. Workaround:
- Set `META_PAGE_ID` manually in `.env`
- Use a System User token instead of a User token

### Token Expired

- Short-lived tokens expire after 1-2 hours
- Long-lived tokens expire after 60 days
- Page Access Tokens from System Users don't expire
- **Solution:** Use System User tokens (Step 5.1) for production

### Signature Verification Fails

- Make sure `META_APP_SECRET` is set in `.env`
- The webhook handler skips verification if `APP_SECRET` is empty
- Check that the secret matches what's in the Meta Dashboard

### Comments Not Appearing in Live Feed

1. Check the Flask backend logs for errors
2. Make sure the ML model is loaded (check for `CyberbullyingClassifier` in logs)
3. Test with the `/api/webhook/simulate` endpoint:
   ```bash
   curl -X POST http://localhost:5000/api/webhook/simulate \
     -H "Content-Type: application/json" \
     -d '{"text": "You are stupid", "platform": "facebook", "author": "test"}'
   ```

---

## 14. Meta API Quirks and Known Issues

### 1. Admin Self-Comments Are Ignored

Meta does NOT send webhook events when the Page admin comments on their own posts. This is by design — Meta considers this "self-interaction" and doesn't notify about it.

**Workaround:** Always test from a different Facebook account.

### 2. `/me/accounts` Returns Empty

Even with all correct permissions granted, `GET /me/accounts` may return `{"data": []}`. This happens when:
- The Page isn't properly linked through the OAuth flow
- The token is a Page Access Token (not a User Access Token)
- Business Manager permissions are required

**Workaround:** Set `META_PAGE_ID` manually in `.env`.

### 3. Facebook API Returns Comments Without `message` Field

When fetching comments as a sub-field of feed (`GET /{page_id}/feed?fields=comments`), Facebook may return comments without the `message` field. You must fetch comments per-post:

```bash
GET /{post_id}/comments?fields=message,from,created_time,id
```

### 4. Token Exchange Required

Facebook tokens go through a chain:
1. **Short-lived User Token** (1-2 hours) — from Graph API Explorer
2. **Long-lived User Token** (60 days) — exchange via `/oauth/access_token`
3. **Page Access Token** — from `/me/accounts` or System User

Never use a short-lived token in production.

### 5. Webhook Field Names Differ Between Platforms

- **Facebook Page:** Comments come through the `feed` field
- **Instagram:** Comments come through the `comments` field (separate from feed)
- **Direct Messages:** Come through the `messages` field

### 6. App Review Takes 1-2 Weeks

For Live mode, Meta requires App Review. For testing:
- Use Development mode
- Add test users in App Dashboard > Roles
- Only app admins/developers/testers can trigger events

### 7. ngrok URL Changes on Restart

The free tier of ngrok gives you a new URL each time. If the URL changes:
1. Update the webhook URL in Meta Dashboard
2. Re-verify the webhook
3. The page subscription persists

### 8. Permissions Are Granular

Each permission must be individually requested and approved. If you only request `pages_read_engagement`, you can't delete comments (you'd also need `pages_manage_posts`).

---

## Quick Reference: Complete Setup Checklist

- [ ] Created Meta Developer Account
- [ ] Created Meta App (Business type)
- [ ] Got App ID and App Secret
- [ ] Set up System User in Business Manager
- [ ] Generated long-lived Page Access Token
- [ ] Granted all required permissions
- [ ] Got Page ID
- [ ] Set up ngrok
- [ ] Configured webhook URL in Meta Dashboard
- [ ] Verified webhook (green checkmark)
- [ ] Subscribed to `feed` and `messages` fields
- [ ] **Subscribed Page to App via `subscribed_apps` endpoint** (CRITICAL)
- [ ] Filled in `.env` file
- [ ] Tested webhook verification
- [ ] Tested manual comment fetch
- [ ] Tested webhook events from different account
- [ ] Live Feed auto-refreshes with new comments

---

## Support

If you're stuck:
1. Check the **Troubleshooting** section above
2. Check the Flask backend logs for errors
3. Check the ngrok inspection UI (http://localhost:4040) for incoming requests
4. Use the **Meta API Test** page in the app to diagnose connection issues
