import requests
import json
try:
    res = requests.post("http://empathicgateway-backend-1:8081/chat", json={"text": "Just browsing, thanks for the help!"})
    print(res.text)
except Exception as e: print(e)
