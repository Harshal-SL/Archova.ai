#!/usr/bin/env python3
"""Test Ollama directly to see if it's responding"""

import requests
import json
import time

OLLAMA_URL = "http://localhost:11434/api/generate"

print("Testing Ollama directly...")

prompt = "Generate a simple JSON object with a 'message' field saying hello."

payload = {
    "model": "mistral",
    "prompt": prompt,
    "stream": False,
    "format": "json",
    "options": {"temperature": 0.2, "num_predict": 100}
}

print(f"\nSending request to Ollama...")
print(f"Model: {payload['model']}")
print(f"Prompt: {prompt}")

start = time.time()

try:
    response = requests.post(OLLAMA_URL, json=payload, timeout=60)
    elapsed = time.time() - start
    
    print(f"\n✓ Response received in {elapsed:.2f} seconds")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nResponse keys: {list(data.keys())}")
        print(f"Done: {data.get('done')}")
        print(f"Done reason: {data.get('done_reason')}")
        print(f"\nGenerated text:")
        print(data.get('response', ''))
    else:
        print(f"Error: {response.text}")
        
except requests.exceptions.Timeout:
    print(f"\n✗ Request timed out after 60 seconds")
except Exception as e:
    print(f"\n✗ Error: {e}")
