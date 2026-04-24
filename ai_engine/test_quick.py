#!/usr/bin/env python3
"""Quick test to check if the pipeline is working"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("Testing pipeline...")

# Step 1: Input
print("\n[1] Testing input...")
response = requests.post(f"{BASE_URL}/api/input", data={"text": "Create a simple chat app"})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    prompt = data["combined_prompt"]
    print(f"✓ Input OK")
else:
    print(f"✗ Input failed: {response.text}")
    exit(1)

# Step 2: Extract
print("\n[2] Testing extraction...")
response = requests.post(f"{BASE_URL}/api/extract", json={"combined_prompt": prompt})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    parameters = data["parameters"]
    print(f"✓ Extraction OK - {len(parameters)} parameters")
else:
    print(f"✗ Extraction failed: {response.text}")
    exit(1)

# Step 3: Elicit
print("\n[3] Testing elicitation...")
response = requests.post(f"{BASE_URL}/api/elicit", json={"parameters": parameters, "prompt": prompt})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    questions = data.get("questions", [])
    print(f"✓ Elicitation OK - {len(questions)} questions")
    
    # Auto-answer if questions exist
    if questions:
        answers = [{"parameter": q["parameter"], "answer": q["options"][0]} for q in questions if q.get("options")]
        response = requests.post(f"{BASE_URL}/api/elicit/answer", json={"parameters": parameters, "answers": answers})
        if response.status_code == 200:
            parameters = response.json()["parameters"]
            print(f"✓ Answers merged")
else:
    print(f"✗ Elicitation failed: {response.text}")
    exit(1)

# Step 4: Design
print("\n[4] Testing design generation...")
print("This may take 3-5 minutes...")
try:
    response = requests.post(f"{BASE_URL}/api/design", json={"parameters": parameters}, timeout=360)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Design generation OK")
        print(f"\nDesign output keys: {list(data.keys())}")
        if "design_output" in data:
            print(f"Design output has: {list(data['design_output'].keys())}")
    else:
        print(f"✗ Design failed: {response.text}")
        exit(1)
except requests.exceptions.Timeout:
    print("✗ Design generation timed out after 6 minutes")
    print("Check server logs for errors")
    exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

print("\n✓ All tests passed!")
