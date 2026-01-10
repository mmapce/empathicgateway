import requests
import time
import os

API_URL = "http://localhost:8081"
API_KEY = "empathic-secret-key"

text = """👤 👤 I am a senior retired banker with over 39 years of experience at all counters in the bank. Till nineties the common issue was with the cash counter and crowded counters which got over as the ATMs came on the scene. Now as a customer of the same bank where I worked so long, I find security guard at the entry gate misbehaving with small ticket bankers and hired hand inside the hall having the level of control over operations which ideally is to be done by the second in command in a branch of the Bank, Most painful is the attitude of counter staff. They gave vague replies as their mind is engrossed on their phone to see the Whatsapp messages. The officer like quality in an officer is not seen and commitment to the client which is their primary role is missing. It is time pass and no work culture. So important jobs like safe keeping of keys and operation of lockers is done by temporary hands which is fraught with risks of immense proportions."""

payload = {"text": text}
headers = {"X-API-Key": API_KEY}

print(f"Sending request with {len(text)} chars...")
start = time.time()
try:
    response = requests.post(f"{API_URL}/chat", json=payload, headers=headers, timeout=30) # High timeout for debug
    end = time.time()
    print(f"Status Code: {response.status_code}")
    print(f"Time Taken: {end - start:.2f} seconds")
    print("Response:", response.json())
except Exception as e:
    print(f"Error: {e}")
