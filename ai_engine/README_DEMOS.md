# AI Architecture Engine - Demo Suite

Complete presentation-ready demos for showcasing the end-to-end pipeline.

---

## 🎯 Quick Start

### Fastest Way to Demo
```bash
quick_start_demo.bat
```
Opens browser to http://localhost:7860

### Just CLI
```bash
run_demo_cli.bat
```

### Just GUI
```bash
run_demo_gui.bat
```

---

## 📁 Files Overview

### Demo Scripts
| File | Description | Best For |
|------|-------------|----------|
| `demo_cli.py` | Interactive terminal demo | Technical audiences |
| `demo_gui.py` | Web-based Gradio interface | All audiences |
| `test_pipeline.py` | Automated testing | CI/CD, validation |

### Launchers (Windows)
| File | What It Does |
|------|--------------|
| `run_demo_cli.bat` | Starts CLI demo |
| `run_demo_gui.bat` | Starts GUI demo |
| `quick_start_demo.bat` | Starts server + GUI |

### Documentation
| File | Contents |
|------|----------|
| `PRESENTATION_READY.md` | ⭐ **START HERE** - Complete presentation guide |
| `DEMO_INSTRUCTIONS.md` | Detailed setup and usage |
| `DEMO_COMPARISON.md` | CLI vs GUI comparison |
| `PIPELINE_TEST_RESULTS.md` | Example output |
| `RAG_COMPARISON_ANALYSIS.md` | RAG data explanation |

---

## 🚀 Usage

### 1. Start the Backend Server
```bash
venv\Scripts\activate
uvicorn app.main:app --reload
```

### 2. Choose Your Demo

**For Presentations:**
```bash
quick_start_demo.bat
```

**For Development:**
```bash
python demo_cli.py
```

### 3. Enter Your Prompt
```
Create an e-commerce application for 10k users interacting everyday
```

### 4. View Results
- CLI: Terminal output + JSON file
- GUI: Browser tabs + download button

---

## 📋 Example Prompts

```
Create an e-commerce application for 10k users interacting everyday
```

```
Design a social media platform with photo sharing for 50k daily active users
```

```
Build a real-time messaging system supporting 1000 concurrent users
```

```
Create a video streaming platform for 100k concurrent viewers
```

---

## 🎬 Demo Features

### CLI Demo
- ✅ Colored terminal output
- ✅ Step-by-step execution
- ✅ Interactive question answering
- ✅ Automatic JSON export
- ✅ Progress indicators

### GUI Demo
- ✅ Modern web interface
- ✅ Tabbed result view
- ✅ Auto-select mode
- ✅ Download button
- ✅ Server status check
- ✅ Real-time updates

---

## 🔧 Requirements

### Python Packages
```bash
pip install gradio  # For GUI demo only
```

All other dependencies are in `requirements.txt`

### Running Services
- FastAPI server (port 8000)
- Ollama with your LLM model

---

## 📊 Pipeline Steps

Both demos execute the same 5-step pipeline:

1. **Input Processing** - Parse and validate prompt
2. **Requirements Extraction** - Extract system parameters
3. **Missing Parameter Detection** - Identify gaps
4. **Clarification Questions** - Generate and answer questions
5. **System Design Generation** - Create architecture using RAG

---

## 💡 Tips

### For Best Results
- Use clear, specific prompts
- Include scale information (users, requests, etc.)
- Mention key requirements (real-time, security, etc.)

### For Presentations
- Test beforehand with your actual prompts
- Have 2-3 backup prompts ready
- Use GUI demo for visual appeal
- Use CLI demo for technical depth

### For Development
- Use CLI demo for quick iterations
- Check server logs for debugging
- Save output files for comparison

---

## 🐛 Troubleshooting

### Server Not Running
```bash
venv\Scripts\activate
uvicorn app.main:app --reload
```

### Gradio Not Installed
```bash
venv\Scripts\pip install gradio
```

### Port Already in Use
- Change port in demo files
- Or kill existing process

### Design Takes Too Long
- Normal: 30-60 seconds
- Check Ollama is running
- Verify model is loaded

---

## 📖 Documentation

- **Start Here**: `PRESENTATION_READY.md`
- **Detailed Guide**: `DEMO_INSTRUCTIONS.md`
- **Comparison**: `DEMO_COMPARISON.md`
- **Example Output**: `PIPELINE_TEST_RESULTS.md`

---

## 🎯 Use Cases

### Presentations
- Client demos
- Team meetings
- Conference talks
- Video recordings

### Development
- Testing new prompts
- Validating pipeline
- Debugging issues
- Comparing outputs

### Education
- Teaching system design
- Demonstrating RAG
- Showing LLM applications
- Architecture workshops

---

## 📈 Output

### CLI Demo
- Terminal output with colors
- JSON file: `demo_output_TIMESTAMP.json`

### GUI Demo
- Browser interface with tabs
- Downloadable JSON
- Markdown-formatted results

### Both Include
- Extracted parameters
- Generated questions
- High-level design
- Low-level design
- RAG references
- Complete JSON

---

## 🔄 Workflow

```
User Prompt
    ↓
Input Processing
    ↓
Requirements Extraction
    ↓
Missing Parameter Detection
    ↓
Clarification Questions ← User Answers
    ↓
System Design Generation (RAG-enhanced)
    ↓
Complete Architecture
```

---

## ✨ Features

- **RAG-Enhanced**: Uses 300+ architecture patterns
- **Interactive**: Asks clarifying questions
- **Complete**: Generates HLD + LLD
- **Fast**: Results in under 60 seconds
- **Flexible**: CLI or GUI interface
- **Exportable**: JSON output for integration

---

## 🎓 Learning Resources

1. Run the demos with different prompts
2. Compare outputs for similar systems
3. Review the RAG references used
4. Examine the generated architectures
5. Read the documentation files

---

## 📞 Need Help?

1. Check `DEMO_INSTRUCTIONS.md` for detailed help
2. Review `PRESENTATION_READY.md` for presentation tips
3. See `DEMO_COMPARISON.md` for feature comparison
4. Look at `PIPELINE_TEST_RESULTS.md` for examples

---

## 🎉 Ready to Present!

Everything is set up and tested. Just run:
```bash
quick_start_demo.bat
```

And you're ready to showcase the AI Architecture Engine!

---

**Made with ❤️ for presenting awesome AI-powered system design**
