#!/usr/bin/env python3
"""
Interactive CLI Demo for AI Architecture Engine Pipeline
Demonstrates the complete end-to-end workflow with user interaction
"""

import requests
import json
import sys
from typing import Dict, List, Any
from datetime import datetime

BASE_URL = "http://localhost:8000"

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text: str):
    """Print a styled header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.END}\n")

def print_step(step_num: int, title: str):
    """Print a step header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}[STEP {step_num}] {title}{Colors.END}")
    print(f"{Colors.BLUE}{'-' * 80}{Colors.END}")

def print_success(message: str):
    """Print a success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str):
    """Print an error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message: str):
    """Print an info message"""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")

def check_server():
    """Check if the FastAPI server is running"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False

def step1_input(prompt: str) -> Dict[str, Any]:
    """Step 1: Process input prompt"""
    print_step(1, "Processing Input")
    
    response = requests.post(
        f"{BASE_URL}/api/input",
        data={"text": prompt}
    )
    
    if response.status_code != 200:
        print_error(f"Failed to process input: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    data = response.json()
    print_success("Input processed successfully")
    print(f"  {Colors.CYAN}Sources:{Colors.END} {', '.join(data['sources'])}")
    print(f"  {Colors.CYAN}Prompt:{Colors.END} {data['combined_prompt'][:100]}...")
    
    return data

def step2_extract(combined_prompt: str) -> Dict[str, Any]:
    """Step 2: Extract requirements"""
    print_step(2, "Extracting Requirements")
    print_info("Analyzing prompt and extracting system parameters...")
    
    response = requests.post(
        f"{BASE_URL}/api/extract",
        json={"combined_prompt": combined_prompt}
    )
    
    if response.status_code != 200:
        print_error(f"Failed to extract requirements: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    data = response.json()
    parameters = data["parameters"]
    
    print_success(f"Extracted {len(parameters)} parameters")
    print(f"\n{Colors.BOLD}Extracted Parameters:{Colors.END}")
    
    for key, value in parameters.items():
        val = value.get('value')
        if val:
            if isinstance(val, list):
                print(f"  {Colors.CYAN}• {key}:{Colors.END}")
                for item in val[:3]:  # Show first 3 items
                    print(f"    - {item}")
                if len(val) > 3:
                    print(f"    ... and {len(val) - 3} more")
            else:
                display_val = str(val)[:80]
                print(f"  {Colors.CYAN}• {key}:{Colors.END} {display_val}")
    
    return data

def step3_elicit(parameters: Dict, prompt: str) -> Dict[str, Any]:
    """Step 3: Elicit missing requirements"""
    print_step(3, "Eliciting Missing Requirements")
    print_info("Detecting missing parameters and generating questions...")
    
    response = requests.post(
        f"{BASE_URL}/api/elicit",
        json={
            "parameters": parameters,
            "prompt": prompt
        }
    )
    
    if response.status_code != 200:
        print_error(f"Failed to elicit requirements: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    data = response.json()
    
    if "questions" in data and data["questions"]:
        print_success(f"Generated {len(data['questions'])} clarification questions")
        return data
    else:
        print_success("No missing parameters detected - all requirements extracted!")
        return data

def step4_answer(parameters: Dict, questions: List[Dict]) -> Dict[str, Any]:
    """Step 4: Collect and submit answers"""
    print_step(4, "Answering Clarification Questions")
    
    answers = []
    
    for i, q in enumerate(questions, 1):
        param = q.get("parameter", "unknown")
        question_text = q.get("question", "")
        options = q.get("options", [])
        
        print(f"\n{Colors.BOLD}Question {i}/{len(questions)}:{Colors.END}")
        print(f"{Colors.YELLOW}Parameter:{Colors.END} {param}")
        print(f"{Colors.YELLOW}Question:{Colors.END} {question_text}\n")
        
        if options:
            for j, opt in enumerate(options, 1):
                print(f"  {Colors.GREEN}{j}.{Colors.END} {opt}")
            
            while True:
                try:
                    choice = input(f"\n{Colors.BOLD}Select option (1-{len(options)}):{Colors.END} ").strip()
                    choice_idx = int(choice) - 1
                    
                    if 0 <= choice_idx < len(options):
                        selected = options[choice_idx]
                        answers.append({
                            "parameter": param,
                            "answer": selected
                        })
                        print_success(f"Selected: {selected[:80]}...")
                        break
                    else:
                        print_error(f"Please enter a number between 1 and {len(options)}")
                except ValueError:
                    print_error("Please enter a valid number")
                except KeyboardInterrupt:
                    print("\n")
                    print_error("Demo cancelled by user")
                    sys.exit(0)
        else:
            # Free text answer
            answer = input(f"{Colors.BOLD}Your answer:{Colors.END} ").strip()
            answers.append({
                "parameter": param,
                "answer": answer
            })
    
    # Submit answers
    print_info("\nSubmitting answers...")
    response = requests.post(
        f"{BASE_URL}/api/elicit/answer",
        json={
            "parameters": parameters,
            "answers": answers
        }
    )
    
    if response.status_code != 200:
        print_error(f"Failed to submit answers: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    data = response.json()
    print_success("Answers merged successfully")
    
    return data

def step5_design(parameters: Dict) -> Dict[str, Any]:
    """Step 5: Generate system design"""
    print_step(5, "Generating System Design")
    print_info("Creating architecture design using RAG-enhanced LLM...")
    print_info("This may take 30-60 seconds...")
    
    response = requests.post(
        f"{BASE_URL}/api/design",
        json={"parameters": parameters},
        timeout=300
    )
    
    if response.status_code != 200:
        print_error(f"Failed to generate design: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    data = response.json()
    print_success("System design generated successfully!")
    
    return data

def display_design_summary(design_data: Dict):
    """Display a summary of the generated design"""
    print_header("SYSTEM DESIGN SUMMARY")
    
    design_output = design_data.get("design_output", {})
    hld = design_output.get("high_level_design", {})
    lld = design_output.get("low_level_design", {})
    references = design_output.get("references", [])
    
    # High-Level Design
    print(f"{Colors.BOLD}{Colors.CYAN}High-Level Design:{Colors.END}")
    print(f"  {Colors.YELLOW}System Name:{Colors.END} {hld.get('system_name', 'N/A')}")
    print(f"  {Colors.YELLOW}Version:{Colors.END} {hld.get('version', 'N/A')}")
    print(f"  {Colors.YELLOW}Description:{Colors.END} {hld.get('description', 'N/A')}")
    
    arch = hld.get('architecture', {})
    if arch:
        print(f"\n  {Colors.YELLOW}Architecture:{Colors.END}")
        print(f"    Type: {arch.get('type', 'N/A')}")
        print(f"    Patterns: {', '.join(arch.get('pattern', []))}")
        print(f"    Deployment: {arch.get('deployment', 'N/A')}")
    
    components = hld.get('core_components', [])
    if components:
        print(f"\n  {Colors.YELLOW}Core Components ({len(components)}):{Colors.END}")
        for comp in components:
            print(f"    • {Colors.GREEN}{comp.get('name')}{Colors.END} ({comp.get('type')})")
            print(f"      Tech: {', '.join(comp.get('technology_options', []))}")
    
    # Scalability
    scalability = hld.get('scalability', {})
    if scalability:
        print(f"\n  {Colors.YELLOW}Scalability:{Colors.END}")
        print(f"    Approach: {scalability.get('approach', 'N/A')}")
        print(f"    Load Balancer: {scalability.get('load_balancer', 'N/A')}")
        print(f"    Auto-scaling: {scalability.get('auto_scaling', 'N/A')}")
    
    # Security
    security = hld.get('security', {})
    if security:
        print(f"\n  {Colors.YELLOW}Security:{Colors.END}")
        print(f"    Authentication: {security.get('authentication', 'N/A')}")
        print(f"    Authorization: {security.get('authorization', 'N/A')}")
    
    # References
    if references:
        print(f"\n{Colors.BOLD}{Colors.CYAN}Knowledge Base References:{Colors.END}")
        for ref in references:
            source = ref.get('source', 'N/A')
            relevance = ref.get('why_relevant', 'N/A')
            print(f"  • {Colors.GREEN}{source}{Colors.END}")
            print(f"    {relevance}")
    
    # Low-Level Design
    lld_components = lld.get('components', [])
    if lld_components:
        print(f"\n{Colors.BOLD}{Colors.CYAN}Low-Level Design Components:{Colors.END} {len(lld_components)} detailed components")

def save_output(all_data: Dict, prompt: str):
    """Save the complete output to a file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"demo_output_{timestamp}.json"
    
    output = {
        "timestamp": timestamp,
        "original_prompt": prompt,
        "pipeline_data": all_data
    }
    
    with open(filename, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{Colors.GREEN}✓ Complete output saved to: {filename}{Colors.END}")
    return filename

def main():
    """Main demo function"""
    print_header("AI ARCHITECTURE ENGINE - INTERACTIVE DEMO")
    
    # Check server
    print_info("Checking server connection...")
    if not check_server():
        print_error("FastAPI server is not running!")
        print_info("Please start the server with: uvicorn app.main:app --reload")
        sys.exit(1)
    print_success("Server is running")
    
    # Get user prompt
    print(f"\n{Colors.BOLD}Enter your system design prompt:{Colors.END}")
    print(f"{Colors.YELLOW}Example: Create an e-commerce application for 10k users{Colors.END}")
    
    try:
        prompt = input(f"{Colors.BOLD}Your prompt:{Colors.END} ").strip()
    except KeyboardInterrupt:
        print("\n")
        print_error("Demo cancelled by user")
        sys.exit(0)
    
    if not prompt:
        print_error("Prompt cannot be empty!")
        sys.exit(1)
    
    print(f"\n{Colors.GREEN}Starting pipeline with prompt:{Colors.END} {prompt}")
    
    # Execute pipeline
    all_data = {}
    
    # Step 1: Input
    input_data = step1_input(prompt)
    all_data['input'] = input_data
    combined_prompt = input_data['combined_prompt']
    
    # Step 2: Extract
    extract_data = step2_extract(combined_prompt)
    all_data['extraction'] = extract_data
    parameters = extract_data['parameters']
    
    # Step 3: Elicit
    elicit_data = step3_elicit(parameters, combined_prompt)
    all_data['elicitation'] = elicit_data
    
    # Step 4: Answer (if questions exist)
    if "questions" in elicit_data and elicit_data["questions"]:
        answer_data = step4_answer(parameters, elicit_data["questions"])
        all_data['answers'] = answer_data
        parameters = answer_data['parameters']
    
    # Step 5: Design
    design_data = step5_design(parameters)
    all_data['design'] = design_data
    
    # Display summary
    display_design_summary(design_data)
    
    # Save output
    output_file = save_output(all_data, prompt)
    
    # Final message
    print_header("DEMO COMPLETED SUCCESSFULLY")
    print(f"{Colors.GREEN}✓ All pipeline steps executed{Colors.END}")
    print(f"{Colors.GREEN}✓ System design generated{Colors.END}")
    print(f"{Colors.GREEN}✓ Output saved to {output_file}{Colors.END}")
    print(f"\n{Colors.BOLD}Thank you for using AI Architecture Engine!{Colors.END}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        print_error("Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
