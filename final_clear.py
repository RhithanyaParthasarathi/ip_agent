import requests
try:
    r = requests.post('http://localhost:8000/collection/clear')
    print(r.json())
except Exception as e:
    print(f"Error: {e}")
