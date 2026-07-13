#!/usr/bin/env python3
"""
Web-based GUI Demo for AI Architecture Engine Pipeline
Simple Gradio interface for presenting the end-to-end workflow
"""

import gradio as gr
import requests
import json
from typing import Dict, List, Tuple, Any
from datetime import datetime

BASE_URL = "http://localhost:8000"

def check_server() -> Tuple[bool, str]:
    """Check if the FastAPI server is running"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        if response.status_code == 200:
            return True, "✅ Server is running"
        return False, f"❌ Server returned status {response.status_code}"
    except Exception as e:
        return False, f"❌ Cannot connect to server: {str(e)}"

def process_pipeline(prompt: str, auto_select: bool = False) -> Tuple[str, str, str, str, str, str]:
    """
    Process the complete pipeline
    Returns: (status, extraction, elicitation, questions_html, design_summary, full_json)
    """
    if not prompt.strip():
        return "❌ Error: Prompt cannot be empty", "", "", "", "", ""
    
    try:
        # Step 1: Input
        status = "🔄 Step 1/5: Processing input..."
        input_response = requests.post(
            f"{BASE_URL}/api/input",
            data={"text": prompt}
        )
        
        if input_response.status_code != 200:
            return f"❌ Step 1 Failed: {input_response.text}", "", "", "", "", ""
        
        input_data = input_response.json()
        combined_prompt = input_data["combined_prompt"]
        
        # Step 2: Extract
        status = "🔄 Step 2/5: Extracting requirements..."
        extract_response = requests.post(
            f"{BASE_URL}/api/extract",
            json={"combined_prompt": combined_prompt}
        )
        
        if extract_response.status_code != 200:
            return f"❌ Step 2 Failed: {extract_response.text}", "", "", "", "", ""
        
        extract_data = extract_response.json()
        parameters = extract_data["parameters"]
        
        # Format extraction output
        extraction_md = "## 📋 Extracted Parameters\n\n"
        for key, value in parameters.items():
            val = value.get('value')
            if val:
                if isinstance(val, list):
                    extraction_md += f"**{key}:**\n"
                    for item in val[:5]:
                        extraction_md += f"- {item}\n"
                    if len(val) > 5:
                        extraction_md += f"- ... and {len(val) - 5} more\n"
                else:
                    extraction_md += f"**{key}:** {val}\n"
                extraction_md += "\n"
        
        # Step 3: Elicit
        status = "🔄 Step 3/5: Detecting missing requirements..."
        elicit_response = requests.post(
            f"{BASE_URL}/api/elicit",
            json={
                "parameters": parameters,
                "prompt": combined_prompt
            }
        )
        
        if elicit_response.status_code != 200:
            return f"❌ Step 3 Failed: {elicit_response.text}", extraction_md, "", "", "", ""
        
        elicit_data = elicit_response.json()
        questions = elicit_data.get("questions", [])
        
        elicitation_md = f"## 🔍 Missing Parameters\n\n"
        if questions:
            elicitation_md += f"Found **{len(questions)}** missing parameters that need clarification.\n"
        else:
            elicitation_md += "✅ No missing parameters - all requirements extracted!\n"
        
        # Generate questions HTML for interactive selection
        questions_html = ""
        if questions and not auto_select:
            questions_html = "<div style='padding: 20px; background: #f5f5f5; border-radius: 8px;'>"
            questions_html += "<h3>📝 Please Answer the Following Questions:</h3>"
            
            for i, q in enumerate(questions):
                param = q.get("parameter", "unknown")
                question_text = q.get("question", "")
                options = q.get("options", [])
                
                questions_html += f"<div style='margin: 20px 0; padding: 15px; background: white; border-radius: 5px;'>"
                questions_html += f"<h4>Question {i+1}: {param}</h4>"
                questions_html += f"<p><strong>{question_text}</strong></p>"
                
                if options:
                    questions_html += "<ul>"
                    for j, opt in enumerate(options, 1):
                        questions_html += f"<li><strong>Option {j}:</strong> {opt}</li>"
                    questions_html += "</ul>"
                
                questions_html += "</div>"
            
            questions_html += "</div>"
            
            # Return early for manual selection
            return (
                "⏸️ Waiting for user input...",
                extraction_md,
                elicitation_md,
                questions_html,
                "",
                json.dumps({
                    "input": input_data,
                    "extraction": extract_data,
                    "elicitation": elicit_data,
                    "status": "awaiting_answers"
                }, indent=2)
            )
        
        # Step 4: Auto-answer or skip if no questions
        if questions and auto_select:
            status = "🔄 Step 4/5: Auto-selecting option 1 for all questions..."
            answers = []
            for q in questions:
                options = q.get("options", [])
                if options:
                    answers.append({
                        "parameter": q.get("parameter"),
                        "answer": options[0]  # Always select first option
                    })
            
            answer_response = requests.post(
                f"{BASE_URL}/api/elicit/answer",
                json={
                    "parameters": parameters,
                    "answers": answers
                }
            )
            
            if answer_response.status_code != 200:
                return f"❌ Step 4 Failed: {answer_response.text}", extraction_md, elicitation_md, "", "", ""
            
            answer_data = answer_response.json()
            parameters = answer_data["parameters"]
        
        # Step 5: Design
        status = "🔄 Step 5/5: Generating system design (this may take 3-5 minutes)..."
        design_response = requests.post(
            f"{BASE_URL}/api/design",
            json={"parameters": parameters},
            timeout=360  # 6 minutes to be safe
        )
        
        if design_response.status_code != 200:
            return f"❌ Step 5 Failed: {design_response.text}", extraction_md, elicitation_md, "", "", ""
        
        design_data = design_response.json()
        
        # Format design summary
        design_summary = format_design_summary(design_data)
        
        # Complete JSON output
        full_output = {
            "timestamp": datetime.now().isoformat(),
            "original_prompt": prompt,
            "input": input_data,
            "extraction": extract_data,
            "elicitation": elicit_data,
            "design": design_data
        }
        
        return (
            "✅ Pipeline completed successfully!",
            extraction_md,
            elicitation_md,
            "",
            design_summary,
            json.dumps(full_output, indent=2)
        )
        
    except Exception as e:
        return f"❌ Error: {str(e)}", "", "", "", "", ""

def format_design_summary(design_data: Dict) -> str:
    """Format the design output as markdown"""
    md = "## 🏗️ System Design\n\n"
    
    design_output = design_data.get("design_output", {})
    hld = design_output.get("high_level_design", {})
    lld = design_output.get("low_level_design", {})
    references = design_output.get("references", [])
    
    # High-Level Design
    md += "### High-Level Design\n\n"
    md += f"**System Name:** {hld.get('system_name', 'N/A')}\n\n"
    md += f"**Version:** {hld.get('version', 'N/A')}\n\n"
    md += f"**Description:** {hld.get('description', 'N/A')}\n\n"
    
    arch = hld.get('architecture', {})
    if arch:
        md += "#### Architecture\n"
        md += f"- **Type:** {arch.get('type', 'N/A')}\n"
        md += f"- **Patterns:** {', '.join(arch.get('pattern', []))}\n"
        md += f"- **Deployment:** {arch.get('deployment', 'N/A')}\n\n"
    
    components = hld.get('core_components', [])
    if components:
        md += f"#### Core Components ({len(components)})\n\n"
        for comp in components:
            md += f"**{comp.get('name')}** ({comp.get('type')})\n"
            md += f"- Description: {comp.get('description', 'N/A')}\n"
            md += f"- Technologies: {', '.join(comp.get('technology_options', []))}\n"
            md += f"- Interacts with: {', '.join(comp.get('interacts_with', []))}\n\n"
    
    scalability = hld.get('scalability', {})
    if scalability:
        md += "#### Scalability\n"
        md += f"- **Approach:** {scalability.get('approach', 'N/A')}\n"
        md += f"- **Load Balancer:** {scalability.get('load_balancer', 'N/A')}\n"
        md += f"- **Auto-scaling:** {scalability.get('auto_scaling', 'N/A')}\n\n"
    
    security = hld.get('security', {})
    if security:
        md += "#### Security\n"
        md += f"- **Authentication:** {security.get('authentication', 'N/A')}\n"
        md += f"- **Authorization:** {security.get('authorization', 'N/A')}\n"
        md += f"- **Data Security:** {', '.join(security.get('data_security', []))}\n\n"
    
    nfr = hld.get('non_functional_requirements', {})
    if nfr:
        md += "#### Non-Functional Requirements\n"
        md += f"- **Availability:** {nfr.get('availability', 'N/A')}\n"
        md += f"- **Latency:** {nfr.get('latency', 'N/A')}\n"
        md += f"- **Throughput:** {nfr.get('throughput', 'N/A')}\n"
        md += f"- **Fault Tolerance:** {nfr.get('fault_tolerance', 'N/A')}\n\n"
    
    # References
    if references:
        md += "### 📚 Knowledge Base References\n\n"
        for ref in references:
            source = ref.get('source', 'N/A')
            relevance = ref.get('why_relevant', 'N/A')
            md += f"- **{source}**\n  - {relevance}\n\n"
    
    # Low-Level Design
    lld_components = lld.get('components', [])
    if lld_components:
        md += f"### Low-Level Design\n\n"
        md += f"Generated **{len(lld_components)}** detailed component specifications.\n\n"
    
    return md

def create_demo_interface():
    """Create the Gradio interface"""
    
    with gr.Blocks(title="AI Architecture Engine Demo") as demo:
        gr.Markdown("""
        # 🚀 AI Architecture Engine - Interactive Demo
        
        Generate complete system designs from natural language prompts using RAG-enhanced LLM.
        
        **Pipeline Steps:**
        1. 📝 Input Processing
        2. 📋 Requirements Extraction
        3. 🔍 Missing Parameter Detection
        4. 💬 Clarification Questions
        5. 🏗️ System Design Generation
        """)
        
        with gr.Row():
            with gr.Column():
                server_status = gr.Textbox(
                    label="Server Status",
                    value="Checking...",
                    interactive=False
                )
                check_btn = gr.Button("🔄 Check Server", size="sm")
        
        gr.Markdown("---")
        
        with gr.Row():
            prompt_input = gr.Textbox(
                label="System Design Prompt",
                placeholder="Example: Create an e-commerce application for 10k users interacting everyday",
                lines=3
            )
        
        with gr.Row():
            auto_select_checkbox = gr.Checkbox(
                label="Auto-select Option 1 for all questions",
                value=True,
                info="If unchecked, you'll need to manually answer questions"
            )
        
        with gr.Row():
            run_btn = gr.Button("▶️ Run Pipeline", variant="primary", size="lg")
            clear_btn = gr.Button("🗑️ Clear", size="lg")
        
        status_output = gr.Textbox(label="Status", interactive=False)
        
        with gr.Tabs():
            with gr.Tab("📋 Extraction"):
                extraction_output = gr.Markdown()
            
            with gr.Tab("🔍 Elicitation"):
                elicitation_output = gr.Markdown()
                questions_output = gr.HTML()
            
            with gr.Tab("🏗️ Design"):
                design_output = gr.Markdown()
            
            with gr.Tab("📄 Full JSON"):
                json_output = gr.Code(language="json", label="Complete Pipeline Output")
        
        with gr.Row():
            download_btn = gr.Button("💾 Download Results", size="sm")
        
        # Event handlers
        def check_server_status():
            is_running, message = check_server()
            return message
        
        check_btn.click(
            fn=check_server_status,
            outputs=server_status
        )
        
        run_btn.click(
            fn=process_pipeline,
            inputs=[prompt_input, auto_select_checkbox],
            outputs=[
                status_output,
                extraction_output,
                elicitation_output,
                questions_output,
                design_output,
                json_output
            ]
        )
        
        clear_btn.click(
            fn=lambda: ("", "", "", "", "", "", ""),
            outputs=[
                prompt_input,
                status_output,
                extraction_output,
                elicitation_output,
                questions_output,
                design_output,
                json_output
            ]
        )
        
        # Initial server check
        demo.load(
            fn=check_server_status,
            outputs=server_status
        )
        
        gr.Markdown("""
        ---
        ### 💡 Tips:
        - Make sure the FastAPI server is running: `uvicorn app.main:app --reload`
        - The design generation step may take 30-60 seconds
        - Check the "Full JSON" tab for complete output
        - Use auto-select for quick demos, uncheck for interactive mode
        """)
    
    return demo

if __name__ == "__main__":
    demo = create_demo_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7862,
        share=False,
        show_error=True,
        theme=gr.themes.Soft()
    )
