import requests
try:
    r = requests.get("https://api.exchangerate.host/convert", params={"from":"USD","to":"EUR","amount":1}, timeout=5)
    r.raise_for_status()
    print("OK, API responde:", r.json())
except Exception as e:
    print("API error:", e)
