import requests
r = requests.post("https://cyberguard-634541519354.asia-southeast1.run.app/api/auth/login", json={"username": "Zohaib", "password": "zohaib123"})
print(f"Status: {r.status_code}")
if r.ok:
    data = r.json()
    print(f"Login OK - Role: {data['user']['role']}, Tenant: {data['user']['tenant_id']}")
else:
    print(f"Error: {r.text}")
