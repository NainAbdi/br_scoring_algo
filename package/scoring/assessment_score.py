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
    breakdown: Dict[str, float]  # Legacy breakdown for backward compatibility
    
    # New skill-based scoring structure
    skill_scores: Optional[Dict[str, float]] = None  # {"technical_expertise": 0.85, "problem_solving": 0.72, "communication": 0.68}
    component_breakdown: Optional[Dict[str, Dict[str, float]]] = None  # Detailed breakdown for each skill
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format, including both legacy and new structure."""
        result = {
            "assessment_id": self.assessment_id,
            "total_score": self.total_score,
            "breakdown": self.breakdown
        }
        
        # Add new skill-based structure if available
        if self.skill_scores is not None:
            result["skill_scores"] = self.skill_scores
        if self.component_breakdown is not None:
            result["component_breakdown"] = self.component_breakdown
            
        return result
    
    def get_skill_score(self, skill_name: str) -> Optional[float]:
        """Get score for a specific skill."""
        if self.skill_scores is not None:
            return self.skill_scores.get(skill_name)
        return None
    
    def get_component_breakdown(self, skill_name: str) -> Optional[Dict[str, float]]:
        """Get component breakdown for a specific skill."""
        if self.component_breakdown is not None:
            return self.component_breakdown.get(skill_name)
        return None 