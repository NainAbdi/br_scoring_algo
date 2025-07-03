from typing import Dict, List

# Skill-based scoring configuration
SKILL_SCORING_CONFIG: Dict[str, Dict] = {
    "technical_expertise": {
        "components": ["main_question_score", "time_performance", "written_answers"],
        "weights": [0.4, 0.2, 0.4],  # 40% main question, 20% time, 40% written
        "written_answer_criteria": ["technical_accuracy"]  # Only technical accuracy counts
    },
    "problem_solving": {
        "components": ["written_answers"],
        "weights": [1.0],
        "written_answer_criteria": ["problem_solving_methodology", "logical_thinking"]
    },
    "communication": {
        "components": ["written_answers"],
        "weights": [1.0],
        "written_answer_criteria": ["clarity", "presentation"]
    }
}

# Legacy scoring weights (for backward compatibility)
SCORING_WEIGHTS: Dict[str, float] = {
    "time": 0.2,
    "main_question": 0.3,
    "written_answers": 0.5
}

# Maximum allowed time for assessment (1 hour in seconds)
MAX_ALLOWED_TIME: int = 3600

# Gemini API configuration
GEMINI_MODEL_NAME: str = "gemini-1.5-flash"

# Enhanced written answer evaluation criteria
WRITTEN_ANSWER_CRITERIA: Dict[str, float] = {
    "technical_accuracy": 0.25,      # Technical knowledge and correctness
    "problem_solving_methodology": 0.25,  # How they approach and solve problems
    "logical_thinking": 0.25,        # Logical reasoning and structure
    "clarity": 0.15,                 # Clear and understandable explanation
    "presentation": 0.10             # Well-structured and organized response
}

# Legacy written answer criteria (for backward compatibility)
LEGACY_WRITTEN_ANSWER_CRITERIA: Dict[str, float] = {
    "technical_accuracy": 0.6,
    "clarity": 0.4
}

def validate_skill_config(config: Dict) -> bool:
    """
    Validate that the skill scoring configuration is properly structured.
    """
    try:
        for skill_name, settings in config.items():
            # Check required keys
            required_keys = ["components", "weights", "written_answer_criteria"]
            for key in required_keys:
                if key not in settings:
                    raise ValueError(f"Missing required key '{key}' in skill '{skill_name}'")
            
            # Validate weights sum to 1.0
            if abs(sum(settings["weights"]) - 1.0) > 0.001:
                raise ValueError(f"Weights for skill '{skill_name}' must sum to 1.0, got {sum(settings['weights'])}")
            
            # Validate components and weights have same length
            if len(settings["components"]) != len(settings["weights"]):
                raise ValueError(f"Components and weights must have same length for skill '{skill_name}'")
            
            # Validate written answer criteria exist in main criteria
            for criterion in settings["written_answer_criteria"]:
                if criterion not in WRITTEN_ANSWER_CRITERIA:
                    raise ValueError(f"Unknown written answer criterion '{criterion}' in skill '{skill_name}'")
        
        return True
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return False

# Validate configuration on import
if not validate_skill_config(SKILL_SCORING_CONFIG):
    raise ValueError("Invalid skill scoring configuration") 