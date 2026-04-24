# ⚡ ULTRA SPEED MODE - Under 300 Seconds

## Latest Optimizations Applied

### Aggressive Speed Settings

#### 1. Reduced Token Generation
- `num_predict`: 2500 → **1800** tokens
- `num_ctx`: 4096 → **2048** (smaller context)
- `temperature`: 0.2 → **0.1** (more focused)
- `top_k`: 40 → **20** (faster sampling)

#### 2. Minimal RAG Context
- `rag_retrieval_k`: 5 → **3** documents
- `rag_context_docs`: 2 → **1** document
- `rag_context_char_budget`: 2000 → **1000** chars
- Context in prompt: 1500 → **800** chars

#### 3. Ultra-Short Prompt
- Removed all verbose instructions
- Max 10 words per field
- Max 2 items per array
- Target under 1800 chars total

#### 4. No Retries
- `max_retries`: 1 → **0** (no retries for speed)
- If LLM fails, use fallback design immediately

#### 5. Strict Timeout
- `ollama_timeout_seconds`: 300s → **240s** (4 minutes max)

---

## Expected Performance

### Target Timeline
```
[0:00] User enters prompt
[0:05] Steps 1-3 complete (input, extract, elicit)
[0:10] Design generation starts
[4:10] Design complete ✓
Total: ~4 minutes (240 seconds)
```

### Breakdown
- Input processing: ~2s
- Requirements extraction: ~3s
- Elicitation: ~3s
- Answer merging: ~1s
- **Design generation: ~230s (3.8 minutes)**

---

## Trade-offs

### What You Gain ✅
- Faster generation (under 5 minutes)
- More predictable timing
- Less waiting during demos

### What You Lose ⚠️
- Shorter descriptions (10 words max)
- Fewer components (2 per array)
- Less detailed designs
- May use fallback more often

---

## If Still Too Slow

### Option 1: Use Even Smaller Model

Check if you have a smaller model:
```bash
ollama list
```

Try pulling a faster model:
```bash
ollama pull phi
```

Then set it:
```bash
$env:LLM_MODEL="phi"
```

Restart server:
```bash
venv\Scripts\activate
uvicorn app.main:app --reload
```

### Option 2: Pre-generate Designs

Generate designs beforehand for common use cases:

```bash
# Generate e-commerce design
python test_pipeline.py
# Saves to pipeline_test_output.json

# During demo, load pre-generated design
```

### Option 3: Use Fallback Design

The system has a built-in fallback that generates instantly if LLM fails.

Edit `app/services/rag_design/pipeline.py` to always use fallback:

```python
def run_design_pipeline(parameters: dict) -> dict:
    # ... existing code ...
    
    # Force fallback for speed (comment out LLM call)
    # generated = generate_design_from_ollama(...)
    generated = _fallback_design(parameters, retrieval_refs, "Speed optimization")
    
    # ... rest of code ...
```

This gives you instant results (< 1 second) but with generic design.

### Option 4: Increase Hardware Resources

If using Ollama locally:
- Close other applications
- Increase RAM allocation
- Use GPU if available (CUDA/Metal)

Check Ollama settings:
```bash
ollama show mistral
```

### Option 5: Use Streaming Response

Modify to show partial results as they generate:

Edit `app/services/rag_design/generator.py`:
```python
payload = {
    "model": model,
    "prompt": prompt,
    "stream": True,  # Enable streaming
    # ...
}
```

This won't make it faster but shows progress.

---

## Testing Current Speed

Run this to measure actual performance:

```bash
venv\Scripts\python test_speed.py
```

Expected output:
```
[1] Input processing... ✓ Done in 2.1s
[2] Requirements extraction... ✓ Done in 3.2s
[3] Elicitation... ✓ Done in 2.8s
[4] Design generation... ✓ Design complete in 235.4s (3.9 minutes)
✓ Under 4 minutes
Total time: 235.4s (3.9 minutes)
```

---

## Monitoring Performance

### Check Ollama Performance
```bash
# Test Ollama speed
venv\Scripts\python test_ollama_direct.py
```

Should respond in < 5 seconds.

### Check Server Logs
Look for slow operations:
```bash
# In server terminal, watch for:
# - Slow RAG retrieval
# - Slow LLM generation
# - Timeout errors
```

### Check System Resources
- Task Manager → Performance
- CPU usage during generation
- RAM usage (should be < 8GB)
- Disk I/O

---

## Current Configuration Summary

```python
# Token limits
num_predict = 1800  # Reduced for speed
num_ctx = 2048      # Smaller context
temperature = 0.1   # More focused

# RAG settings
rag_retrieval_k = 3           # Fewer documents
rag_context_docs = 1          # Minimal context
rag_context_char_budget = 1000  # Short context

# Timeouts
ollama_timeout_seconds = 240  # 4 minutes max
max_retries = 0               # No retries

# Prompt
- Ultra-short instructions
- Max 10 words per field
- Max 2 items per array
- 800 char context limit
```

---

## Realistic Expectations

### Best Case (Warmed Up)
- Simple prompt: 2-3 minutes
- Complex prompt: 3-4 minutes

### Typical Case
- Any prompt: 3.5-4.5 minutes

### Worst Case (Cold Start)
- First run: 4-5 minutes

### If Over 5 Minutes
Something is wrong:
1. Ollama not warmed up
2. System resources low
3. Model too large
4. Network issues (if using remote Ollama)

---

## Final Recommendations

### For Demos
1. **Always warm up first:**
   ```bash
   venv\Scripts\python warmup_ollama.py
   ```

2. **Use simple prompts:**
   ```
   Create a chat app
   Create an e-commerce app for 10k users
   ```

3. **Have backup ready:**
   - Pre-generated designs
   - Documentation to show
   - Fallback mode enabled

### For Production
1. Use faster model (phi, llama2:7b)
2. Use GPU acceleration
3. Cache common designs
4. Pre-generate for known use cases

---

## Troubleshooting

### Still Over 5 Minutes?

**Check Ollama:**
```bash
venv\Scripts\python test_ollama_direct.py
```

If slow (> 10s), restart Ollama:
```bash
Stop-Process -Name "ollama" -Force
ollama serve
venv\Scripts\python warmup_ollama.py
```

**Check Model Size:**
```bash
ollama list
```

Mistral (4.4GB) is reasonable. If using larger model, switch to smaller.

**Check System:**
- Close Chrome/browsers
- Close other heavy apps
- Check RAM usage
- Check CPU usage

---

## Summary

With these ultra-aggressive optimizations:
- ✅ Target: Under 5 minutes (300s)
- ✅ Typical: 3.5-4.5 minutes (210-270s)
- ✅ Best case: 2-3 minutes (120-180s)

**Key:** Always warm up Ollama first!

```bash
venv\Scripts\python warmup_ollama.py
venv\Scripts\python test_speed.py
```

If still too slow, consider using fallback mode or pre-generated designs for demos.
