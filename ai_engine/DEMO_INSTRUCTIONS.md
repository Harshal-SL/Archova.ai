# AI Architecture Engine - Demo Instructions

This guide explains how to run the interactive demos for presenting the end-to-end pipeline.

---

## 🎯 Available Demo Options

### 1. **CLI Demo** (Terminal-based, Interactive)
- Colorful terminal interface
- Step-by-step execution with user prompts
- Interactive question answering
- Best for: Technical presentations, debugging

### 2. **GUI Demo** (Web-based, Visual)
- Modern web interface using Gradio
- Visual display of all pipeline steps
- Auto-select or manual question answering
- Best for: Client presentations, non-technical audiences

---

## 📋 Prerequisites

### 1. Install Dependencies

Make sure you have all required packages:

```bash
# Activate virtual environment
venv/Scripts/activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Install Gradio for GUI demo
pip install gradio
```

### 2. Start the FastAPI Server

The demos require the backend server to be running:

```bash
# In a separate terminal
venv/Scripts/activate
uvicorn app.main:app --reload
```

Wait for the message: `Uvicorn running on http://127.0.0.1:8000`

---

## 🖥️ Running the CLI Demo

### Start the Demo

```bash
python demo_cli.py
```

### What to Expect

1. **Server Check**: Verifies the backend is running
2. **Prompt Input**: Enter your system design requirement
   - Example: "Create an e-commerce application for 10k users"
3. **Step 1**: Input processing
4. **Step 2**: Requirements extraction (shows extracted parameters)
5. **Step 3**: Missing parameter detection
6. **Step 4**: Interactive questions (if any missing parameters)
   - You'll see multiple-choice options
   - Enter the number of your choice (1, 2, 3, etc.)
7. **Step 5**: System design generation (takes 30-60 seconds)
8. **Summary**: Displays the generated architecture
9. **Output**: Saves complete results to `demo_output_TIMESTAMP.json`

### Example Session

```
================================================================================
                  AI ARCHITECTURE ENGINE - INTERACTIVE DEMO                    
================================================================================

ℹ Checking server connection...
✓ Server is running

Enter your system design prompt:
Example: Create an e-commerce application for 10k users
Your prompt: Create a real-time chat application for 1000 concurrent users

[STEP 1] Processing Input
--------------------------------------------------------------------------------
✓ Input processed successfully
  Sources: text
  Prompt: Create a real-time chat application for 1000 concurrent users...

[STEP 2] Extracting Requirements
--------------------------------------------------------------------------------
ℹ Analyzing prompt and extracting system parameters...
✓ Extracted 11 parameters

Extracted Parameters:
  • goal: Create a real-time chat application
  • core_objectives:
    - Support 1000 concurrent users
  • system_type: Web application
  ...

[STEP 3] Eliciting Missing Requirements
--------------------------------------------------------------------------------
✓ Generated 2 clarification questions

Question 1/2:
Parameter: message_persistence
Question: Should messages be stored permanently or temporarily?

  1. Store all messages permanently in a database
  2. Store messages temporarily (e.g., 30 days)
  3. No persistence - messages only exist in memory

Select option (1-3): 1
✓ Selected: Store all messages permanently in a database

...

[STEP 5] Generating System Design
--------------------------------------------------------------------------------
ℹ Creating architecture design using RAG-enhanced LLM...
✓ System design generated successfully!

================================================================================
                          SYSTEM DESIGN SUMMARY                               
================================================================================
...
```

---

## 🌐 Running the GUI Demo

### Start the Demo

```bash
python demo_gui.py
```

### Access the Interface

1. Wait for the message: `Running on local URL: http://127.0.0.1:7860`
2. Open your browser and go to: **http://localhost:7860**

### Using the Interface

1. **Check Server Status**: Click "🔄 Check Server" to verify backend connection
2. **Enter Prompt**: Type your system design requirement in the text box
3. **Auto-select Mode**: 
   - ✅ Checked: Automatically selects Option 1 for all questions (fast demo)
   - ⬜ Unchecked: Manual question answering (interactive mode)
4. **Run Pipeline**: Click "▶️ Run Pipeline"
5. **View Results**: Switch between tabs:
   - **📋 Extraction**: See extracted parameters
   - **🔍 Elicitation**: View missing parameters and questions
   - **🏗️ Design**: Read the generated system architecture
   - **📄 Full JSON**: Download complete output
6. **Download**: Click "💾 Download Results" to save the output

### GUI Features

- **Real-time Status**: Shows current pipeline step
- **Tabbed Interface**: Organized view of each pipeline stage
- **Markdown Rendering**: Beautiful formatting of design output
- **JSON Export**: Complete data for further analysis
- **Responsive Design**: Works on desktop and tablet

---

## 📝 Example Prompts to Try

### E-commerce
```
Create an e-commerce application for 10k users interacting everyday
```

### Social Media
```
Design a social media platform with photo sharing for 50k daily active users
```

### Real-time Chat
```
Build a real-time messaging system supporting 1000 concurrent users with end-to-end encryption
```

### Video Streaming
```
Create a video streaming platform like Netflix for 100k concurrent viewers
```

### IoT System
```
Design an IoT monitoring system for 10000 sensors sending data every minute
```

### Booking System
```
Build a hotel booking system handling 5000 reservations per day
```

---

## 🎬 Presentation Tips

### For CLI Demo

1. **Prepare Your Terminal**: 
   - Use a large font size (16-18pt)
   - Use a dark theme for better visibility
   - Maximize the terminal window

2. **Practice the Flow**:
   - Have your prompt ready to copy-paste
   - Know which options you'll select
   - Explain each step as it executes

3. **Highlight Key Points**:
   - Show the extracted parameters
   - Explain the clarification questions
   - Walk through the generated architecture

### For GUI Demo

1. **Setup**:
   - Open the GUI before the presentation
   - Have example prompts ready
   - Test the connection beforehand

2. **Presentation Flow**:
   - Start with server status check
   - Enter prompt and explain the requirement
   - Enable auto-select for quick demo
   - Switch between tabs to show each stage
   - Highlight the design summary

3. **Interactive Elements**:
   - Let audience suggest prompts
   - Show different system types
   - Compare designs for similar prompts

---

## 🐛 Troubleshooting

### "Cannot connect to server"
- Make sure FastAPI server is running: `uvicorn app.main:app --reload`
- Check if port 8000 is available
- Verify server is on http://localhost:8000

### "Design generation takes too long"
- Normal: 30-60 seconds for LLM processing
- Check Ollama is running and model is loaded
- Monitor server logs for errors

### "Questions not appearing in GUI"
- Uncheck "Auto-select" option
- Refresh the page
- Check browser console for errors

### "CLI colors not showing"
- Windows: Use Windows Terminal or PowerShell 7+
- Linux/Mac: Should work in any terminal
- Alternative: Use the GUI demo

---

## 📊 Output Files

### CLI Demo Output
- **Filename**: `demo_output_YYYYMMDD_HHMMSS.json`
- **Location**: Current directory
- **Contents**: Complete pipeline data including all steps

### Structure
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "original_prompt": "Your prompt here",
  "pipeline_data": {
    "input": {...},
    "extraction": {...},
    "elicitation": {...},
    "design": {...}
  }
}
```

---

## 🔧 Customization

### Modify CLI Colors
Edit `demo_cli.py` and change the `Colors` class:
```python
class Colors:
    HEADER = '\033[95m'  # Change color codes
    BLUE = '\033[94m'
    # ...
```

### Modify GUI Theme
Edit `demo_gui.py` and change the theme:
```python
with gr.Blocks(theme=gr.themes.Monochrome()) as demo:
    # Options: Soft(), Monochrome(), Glass(), Base()
```

### Change Ports
- **FastAPI**: Edit `BASE_URL` in demo files
- **Gradio**: Change `server_port` in `demo_gui.py`

---

## 📚 Additional Resources

- **Pipeline Documentation**: See `PIPELINE_TEST_RESULTS.md`
- **RAG Comparison**: See `RAG_COMPARISON_ANALYSIS.md`
- **API Documentation**: http://localhost:8000/docs (when server is running)

---

## 🎓 Demo Script Template

### Introduction (1 min)
"Today I'll demonstrate our AI Architecture Engine, which generates complete system designs from natural language prompts using RAG-enhanced LLM technology."

### Pipeline Overview (2 min)
"The pipeline has 5 steps:
1. Input processing
2. Requirements extraction
3. Missing parameter detection
4. Clarification questions
5. System design generation"

### Live Demo (5-7 min)
"Let me show you with a real example..."
[Run the demo with prepared prompt]

### Results Review (3 min)
"As you can see, the system generated:
- High-level architecture with 7 components
- Technology recommendations
- Scalability and security considerations
- Low-level design specifications"

### Q&A (5 min)
"Let's try a prompt from the audience..."

---

## ✅ Pre-Presentation Checklist

- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip install gradio`)
- [ ] FastAPI server running
- [ ] Demo script tested with example prompt
- [ ] Output directory has write permissions
- [ ] Browser open (for GUI demo)
- [ ] Terminal font size increased (for CLI demo)
- [ ] Example prompts prepared
- [ ] Backup plan if server fails

---

**Good luck with your presentation! 🚀**
