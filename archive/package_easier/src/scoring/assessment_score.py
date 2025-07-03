from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class WrittenAnswer:
    question_id: str
    answer: str
    question: str

@dataclass
class AssessmentSubmission:
    time_elapsed: int  # in seconds
    main_question_score: float  # score from 0 to 1
    written_answers: List[WrittenAnswer]
    participant_name: str  # Add required participant name field

@dataclass
class AssessmentScore:
    assessment_id: str
    total_score: float
    breakdown: Dict[str, float]
    
    def to_dict(self) -> Dict:
        return {
            "assessment_id": self.assessment_id,
            "total_score": self.total_score,
            "breakdown": self.breakdown
        } 