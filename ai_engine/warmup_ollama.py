#!/usr/bin/env python3
"""
Warm up Ollama by loading the model into memory
This makes subsequent requests much faster
"""

import requests
import time

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral"

print("=" * 60)
print("Warming up Ollama...")
print("=" * 60)

# Simple warm-up request to load model into memory
payload = {
    "model": MODEL,
    "prompt": "Say 'ready' in JSON format with a status field.",
    "stream": False,
    "format": "json",
    "options": {
        "temperature": 0.2,
        "num_predict": 50
    }
}

print(f"\n[1/2] Loading {MODEL} model into memory...")
print("This may take 30-60 seconds on first load...")

start = time.time()

try:
    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    elapsed = time.time() - start
    
    if response.status_code == 200:
        print(f"✓ Model loaded in {elapsed:.1f} seconds")
        data = response.json()
        print(f"✓ Response: {data.get('response', '')[:100]}")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
        exit(1)
        
except requests.exceptions.Timeout:
    print(f"✗ Timeout after 120 seconds")
    print("Ollama might be stuck. Try restarting it:")
    print("  Stop-Process -Name 'ollama' -Force")
    print("  ollama serve")
    exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

# Second request to verify it's fast now
print(f"\n[2/2] Testing response time...")

start = time.time()
try:
    response = requests.post(OLLAMA_URL, json=payload, timeout=30)
    elapsed = time.time() - start
    
    if response.status_code == 200:
        print(f"✓ Response time: {elapsed:.1f} seconds")
        if elapsed < 10:
            print(f"✓ Ollama is warmed up and ready!")
        else:
            print(f"⚠ Response is slower than expected")
    else:
        print(f"✗ Error: {response.status_code}")
        
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("Warm-up complete! Ollama is ready for demos.")
print("=" * 60)
print("\nYou can now run:")
print("  .\\quick_start_demo.bat")
print("  or")
print("  python demo_cli.py")
print("  or")
print("  python demo_gui.py")
