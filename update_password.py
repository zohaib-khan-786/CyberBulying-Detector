import psycopg2
import bcrypt

DATABASE_URL = "postgresql://aipoweredcyberbullying_user:6YPpURH0i9roU8BkOuJ2y5MnbhutAbCI@dpg-d8kl8drtqb8s73eegvu0-a.singapore-postgres.render.com/aipoweredcyberbullying"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Generate bcrypt hash for admin123
hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")

# Update admin password
cur.execute("UPDATE users SET password_hash = %s WHERE username = 'admin'", (hash,))
conn.commit()

# Verify
cur.execute("SELECT username, role, tenant_id FROM users WHERE username = 'admin'")
row = cur.fetchone()
print(f"Updated: {row[0]} / admin123 (role={row[1]}, tenant={row[2]})")

cur.close()
conn.close()
