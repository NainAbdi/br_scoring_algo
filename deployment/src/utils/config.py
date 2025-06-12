from typing import Dict

# Scoring weights for different components
SCORING_WEIGHTS: Dict[str, float] = {
    "time": 0.2,
    "main_question": 0.3,
    "written_answers": 0.5
}

# Maximum allowed time for assessment (1 hour in seconds)
MAX_ALLOWED_TIME: int = 3600

# Gemini API configuration
GEMINI_MODEL_NAME: str = "models/gemini-2.5-flash-preview-04-17"

# Written answer evaluation criteria
WRITTEN_ANSWER_CRITERIA: Dict[str, float] = {
    "technical_accuracy": 0.6,
    "clarity": 0.4
} 