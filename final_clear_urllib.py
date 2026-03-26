import urllib.request as r
try:
    req = r.Request('http://localhost:8000/collection/clear', method='POST')
    print(r.urlopen(req).read().decode())
except Exception as e:
    import urllib.error
    if isinstance(e, urllib.error.HTTPError):
        print("HTTP Error:", e.code, e.read().decode())
    else:
        print("Error:", e)
