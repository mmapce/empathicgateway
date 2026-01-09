import asyncio
import aiohttp
import time
import random

API_URL = "http://localhost:8081/chat"
API_KEY = "secure-key-123"

# Scenarios
CRITICAL_MSG = {"text": "My card is stolen, block it immediately!"} # Fast Lane
NORMAL_MSG = {"text": "Hello, how are you?"} # Normal Lane (Capacity 2)

async def send_request(session, payload, req_id):
    start = time.time()
    try:
        async with session.post(API_URL, json=payload, headers={"X-API-KEY": API_KEY}) as response:
            data = await response.json()
            duration = time.time() - start
            
            status = response.status
            lane = "UNKNOWN"
            if status == 200:
                lane = "FAST" if data['label'] == "CRITICAL" else "NORMAL"
                print(f"✅ [Req {req_id}] {status} OK | Lane: {lane} | Time: {duration:.2f}s")
            elif status == 429:
                print(f"⛔ [Req {req_id}] 429 BLOCKED | System Overloaded! | Time: {duration:.2f}s")
            else:
                print(f"❌ [Req {req_id}] {status} Error")
                
    except Exception as e:
        print(f"❌ [Req {req_id}] Connection Failed: {e}")

async def run_stress_test():
    print("🚀 Starting Stress Test Simulation...")
    print("🎯 Target: Normal Lane (Capacity: 2 slots)")
    print("⚡ Sending 10 request simultaneously...")
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        # Mixed Traffic: 2 Critical, 8 Normal (to flood Normal lane)
        payloads = [CRITICAL_MSG]*2 + [NORMAL_MSG]*8
        random.shuffle(payloads)
        
        for i, payload in enumerate(payloads):
            tasks.append(send_request(session, payload, i+1))
            
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    # Ensure dependencies are installed
    # pip install aiohttp
    asyncio.run(run_stress_test())
