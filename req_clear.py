import sys
try:
    import requests
    res = requests.post('http://localhost:8000/collection/clear', timeout=10)
    print(f"STATUS: {res.status_code}")
    print(f"TEXT: {res.text}")
except Exception as e:
    print(f"ERROR: {e}")
