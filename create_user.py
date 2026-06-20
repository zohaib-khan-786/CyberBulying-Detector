import psycopg2, bcrypt
DATABASE_URL = "postgresql://aipoweredcyberbullying_user:6YPpURH0i9roU8BkOuJ2y5MnbhutAbCI@dpg-d8kl8drtqb8s73eegvu0-a.singapore-postgres.render.com/aipoweredcyberbullying"
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Check tenants
cur.execute("SELECT id, name FROM tenants")
tenants = cur.fetchall()
print("Tenants:")
for t in tenants:
    print(f"  ID={t[0]} Name={t[1]}")

# Check if user exists
cur.execute("SELECT id, username, role, email, tenant_id FROM users WHERE username = 'zohaib'")
row = cur.fetchone()
if row:
    print(f"\nUser exists: ID={row[0]} Username={row[1]} Role={row[2]} Email={row[3]} Tenant={row[4]}")
else:
    # Create user with role=admin on tenant 3 (or ask)
    hash_pw = bcrypt.hashpw(b"zohaib123", bcrypt.gensalt()).decode("utf-8")
    cur.execute(
        "INSERT INTO users (username, email, password_hash, role, tenant_id, is_active) VALUES (%s, %s, %s, %s, %s, %s)",
        ("zohaib", "zohaib@gmail.com", hash_pw, "admin", 3, True)
    )
    conn.commit()
    print(f"\nCreated user: zohaib / zohaib123 (role=admin, tenant=3)")

cur.close()
conn.close()
