from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class WrittenAnswer:
    question_id: str
    answer_text: str
    question_context: Optional[str] = None

@dataclass
class AssessmentSubmission:
    time_taken: int  # in seconds
    main_question_correct: bool
    written_answers: List[WrittenAnswer]

@dataclass
class AssessmentScore:
    total_score: float
    breakdown: Dict[str, float]
    
    def to_dict(self) -> Dict:
        return {
            "total_score": self.total_score,
            "breakdown": self.breakdown
        } 