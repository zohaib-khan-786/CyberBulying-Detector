import psycopg2, bcrypt
DATABASE_URL = "postgresql://aipoweredcyberbullying_user:6YPpURH0i9roU8BkOuJ2y5MnbhutAbCI@dpg-d8kl8drtqb8s73eegvu0-a.singapore-postgres.render.com/aipoweredcyberbullying"
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# List all users
cur.execute("SELECT id, username, role, email, tenant_id FROM users")
print("Existing users:")
for r in cur.fetchall():
    print(f"  ID={r[0]} Username={r[1]} Role={r[2]} Email={r[3]} Tenant={r[4]}")

# Check tenants
cur.execute("SELECT id, name FROM tenants")
print("\nTenants:")
for r in cur.fetchall():
    print(f"  ID={r[0]} Name={r[1]}")

cur.close()
conn.close()
