import psycopg2
DATABASE_URL = "postgresql://aipoweredcyberbullying_user:6YPpURH0i9roU8BkOuJ2y5MnbhutAbCI@dpg-d8kl8drtqb8s73eegvu0-a.singapore-postgres.render.com/aipoweredcyberbullying"
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
cur.execute("SELECT id, tenant_id, page_id, webhook_verify_token, page_access_token IS NOT NULL AS has_token, is_active FROM meta_credentials WHERE tenant_id = 3")
for row in cur.fetchall():
    print(f"ID={row[0]} Tenant={row[1]} PageID={row[2]} VerifyToken={row[3]} HasToken={row[4]} Active={row[5]}")
cur.close()
conn.close()
