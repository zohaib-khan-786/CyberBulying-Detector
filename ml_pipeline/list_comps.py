import requests
token = 'KGAT_efe8e2594937cb93dbe60f16edb7abd9'
headers = {'Authorization': f'Bearer {token}'}
BASE = 'https://api.kaggle.com/v1'

# Try dataset download instead of competition
# Search for toxic/hate/cyberbullying datasets
r = requests.get(f'{BASE}/datasets/list?search=hate+speech+toxic', headers=headers, timeout=30)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    for d in data[:10]:
        ref = d.get('ref','')
        title = d.get('title','')
        size = d.get('size','')
        print(f'  {ref}: {title} ({size})')
else:
    print(f'No dataset access. Response: {r.text[:200]}')

# Also try the datasets/search endpoint
r2 = requests.get(f'{BASE}/datasets/search?search=toxic+comment', headers=headers, timeout=30)
print(f'\nSearch status: {r2.status_code} response: {r2.text[:300]}')
