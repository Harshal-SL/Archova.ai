from .detector import detect_missing_parameters
from .question_generator import generate_questions


def run_elicitation_pipeline(parameters: dict, prompt: str) -> dict:
    missing = detect_missing_parameters(parameters)

    if not missing:
        return {"missing_parameters": [], "questions": []}

    result = generate_questions(missing, prompt)

    return {
        "missing_parameters": missing,
        "questions": result.get("questions", []),
    }
