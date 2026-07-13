#!/usr/bin/env python3
"""Test the speed of design generation with optimizations"""

import requests
import time

BASE_URL = "http://localhost:8000"

print("Testing optimized pipeline speed...")
print("=" * 60)

# Simple prompt for speed test
prompt = "Create a simple chat app"

# Step 1: Input
print("\n[1] Input processing...")
start = time.time()
response = requests.post(f"{BASE_URL}/api/input", data={"text": prompt})
if response.status_code != 200:
    print(f"Failed: {response.text}")
    exit(1)
data = response.json()
combined_prompt = data["combined_prompt"]
elapsed = time.time() - start
print(f"✓ Done in {elapsed:.1f}s")

# Step 2: Extract
print("\n[2] Requirements extraction...")
start = time.time()
response = requests.post(f"{BASE_URL}/api/extract", json={"combined_prompt": combined_prompt})
if response.status_code != 200:
    print(f"Failed: {response.text}")
    exit(1)
data = response.json()
parameters = data["parameters"]
elapsed = time.time() - start
print(f"✓ Done in {elapsed:.1f}s - {len(parameters)} parameters")

# Step 3: Elicit
print("\n[3] Elicitation...")
start = time.time()
response = requests.post(f"{BASE_URL}/api/elicit", json={"parameters": parameters, "prompt": combined_prompt})
if response.status_code != 200:
    print(f"Failed: {response.text}")
    exit(1)
data = response.json()
questions = data.get("questions", [])
elapsed = time.time() - start
print(f"✓ Done in {elapsed:.1f}s - {len(questions)} questions")

# Auto-answer
if questions:
    answers = [{"parameter": q["parameter"], "answer": q["options"][0]} for q in questions if q.get("options")]
    response = requests.post(f"{BASE_URL}/api/elicit/answer", json={"parameters": parameters, "answers": answers})
    if response.status_code == 200:
        parameters = response.json()["parameters"]

# Step 4: Design (THE SLOW PART)
print("\n[4] Design generation...")
print("Measuring time...")
start_design = time.time()

try:
    response = requests.post(f"{BASE_URL}/api/design", json={"parameters": parameters}, timeout=300)
    elapsed_design = time.time() - start_design
    
    if response.status_code == 200:
        print(f"✓ Design complete in {elapsed_design:.1f}s ({elapsed_design/60:.1f} minutes)")
        
        if elapsed_design < 180:
            print("✓✓ UNDER 3 MINUTES! ✓✓")
        elif elapsed_design < 240:
            print("✓ Under 4 minutes")
        elif elapsed_design < 300:
            print("⚠ Under 5 minutes (acceptable)")
        else:
            print("✗ Over 5 minutes (too slow)")
            
        data = response.json()
        design_output = data.get("design_output", {})
        if "assumptions" in design_output:
            assumptions = design_output.get("assumptions", [])
            if assumptions and "Fallback" in str(assumptions[0]):
                print("⚠ Note: Fallback design was used (LLM failed to generate)")
        
    else:
        print(f"✗ Failed: {response.status_code}")
        print(response.text)
        
except requests.exceptions.Timeout:
    elapsed_design = time.time() - start_design
    print(f"✗ Timeout after {elapsed_design:.1f}s")

print("\n" + "=" * 60)
print(f"Total time: {elapsed_design:.1f}s ({elapsed_design/60:.1f} minutes)")
print("=" * 60)
