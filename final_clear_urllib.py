import urllib.request
import json

try:
    url = 'http://localhost:8000/collection/clear'
    req = urllib.request.Request(url, method='POST')
    with urllib.request.urlopen(req) as response:
        print(response.read().decode())
except Exception as e:
    print(f"Error: {e}")
