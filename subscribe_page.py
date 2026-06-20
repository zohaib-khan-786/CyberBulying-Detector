import psycopg2, requests
DATABASE_URL = "postgresql://aipoweredcyberbullying_user:6YPpURH0i9roU8BkOuJ2y5MnbhutAbCI@dpg-d8kl8drtqb8s73eegvu0-a.singapore-postgres.render.com/aipoweredcyberbullying"
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Get page access token for tenant 3
cur.execute("SELECT page_id, page_access_token FROM meta_credentials WHERE tenant_id = 3")
row = cur.fetchone()
page_id = row[0]
token = row[1]

# Subscribe the page to the app's webhook
url = f"https://graph.facebook.com/v25.0/{page_id}/subscribed_apps"
resp = requests.post(url, params={
    "access_token": token,
    "subscribed_fields": "feed"
})
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")

# Also check current subscriptions
check = requests.get(url, params={"access_token": token})
print(f"\nCurrent subscriptions: {check.text}")

cur.close()
conn.close()
