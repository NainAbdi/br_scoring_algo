import uuid
from typing import Dict, Optional
from .assessment_score import AssessmentSubmission, AssessmentScore, WrittenAnswer
from .gemini_evaluator import GeminiEvaluator
from .skill_scorer import SkillScorer
from utils.config import SCORING_WEIGHTS, MAX_ALLOWED_TIME

class ScoringAlgorithm:
    def __init__(self):
        self.time_weight = SCORING_WEIGHTS["time"]
        self.main_question_weight = SCORING_WEIGHTS["main_question"]
        self.written_answers_weight = SCORING_WEIGHTS["written_answers"]
        self.max_allowed_time = MAX_ALLOWED_TIME
        
        # Initialize skill scorer for new skill-based scoring
        self.skill_scorer = SkillScorer()
    
    async def calculate_total_score(
        self, 
        submission: AssessmentSubmission, 
        gemini_evaluator: GeminiEvaluator,
        use_skill_based_scoring: bool = True
    ) -> AssessmentScore:
        """
        Calculate the total score for an assessment submission.
        
        Args:
            submission: The assessment submission data
            gemini_evaluator: The AI evaluator for written answers
            use_skill_based_scoring: Whether to use new skill-based scoring (default: True)
        
        Returns:
            AssessmentScore with both legacy and skill-based results
        """
        # Generate unique assessment ID
        assessment_id = str(uuid.uuid4())
        
        # Calculate legacy scores for backward compatibility
        legacy_breakdown = await self._calculate_legacy_breakdown(submission, gemini_evaluator)
        legacy_total_score = (
            (legacy_breakdown["time_score"] * self.time_weight) +
            (legacy_breakdown["main_question_score"] * self.main_question_weight) +
            (legacy_breakdown["written_answers_score"] * self.written_answers_weight)
        )
        
        # Initialize result with legacy data
        result = AssessmentScore(
            assessment_id=assessment_id,
            total_score=legacy_total_score,
            breakdown=legacy_breakdown
        )
        
        # Add skill-based scoring if requested
        if use_skill_based_scoring:
            skill_results = await self.skill_scorer.calculate_all_skill_scores(submission, gemini_evaluator)
            
            # Extract skill scores and component breakdowns
            skill_scores = {skill: data["score"] for skill, data in skill_results.items()}
            component_breakdown = {skill: data["components"] for skill, data in skill_results.items()}
            
            # Update the result with skill-based data
            result.skill_scores = skill_scores
            result.component_breakdown = component_breakdown
            
            # Optionally update total score to be average of skill scores
            # result.total_score = sum(skill_scores.values()) / len(skill_scores)
        
        return result
    
    async def _calculate_legacy_breakdown(
        self, 
        submission: AssessmentSubmission, 
        gemini_evaluator: GeminiEvaluator
    ) -> Dict[str, float]:
        """
        Calculate legacy breakdown for backward compatibility.
        """
        # Calculate time score
        time_score = self._calculate_time_score(submission.time_elapsed)
        
        # Calculate main question score (keep on 0-1 scale)
        main_question_score = submission.main_question_score
        
        # Calculate written answers score using legacy evaluation
        written_answers_score = await self._evaluate_written_answers_legacy(
            submission.written_answers, 
            gemini_evaluator
        )
        
        return {
            "time_score": time_score,
            "main_question_score": main_question_score,
            "written_answers_score": written_answers_score
        }
    
    def _calculate_time_score(self, time_elapsed: int) -> float:
        """
        Calculate score based on time taken.
        Faster completion results in higher score.
        """
        if time_elapsed <= self.max_allowed_time:
            return 1.0 - (time_elapsed / self.max_allowed_time)
        return 0.0
    
    async def _evaluate_written_answers_legacy(
        self, 
        answers: list[WrittenAnswer], 
        gemini_evaluator: GeminiEvaluator
    ) -> float:
        """
        Evaluate all written answers using legacy criteria and return average score.
        """
        if not answers:
            return 0.0
        
        total_score = 0
        for answer in answers:
            evaluation = await gemini_evaluator.evaluate_answer(
                answer.answer,
                answer.question,
                use_legacy_criteria=True  # Use legacy evaluation
            )
            total_score += evaluation["total_score"]
        
        return total_score / len(answers)
    
    def get_skill_score(self, assessment_score: AssessmentScore, skill_name: str) -> Optional[float]:
        """
        Get score for a specific skill from an assessment result.
        """
        return assessment_score.get_skill_score(skill_name)
    
    def get_skill_breakdown(self, assessment_score: AssessmentScore, skill_name: str) -> Optional[Dict[str, float]]:
        """
        Get component breakdown for a specific skill from an assessment result.
        """
        return assessment_score.get_component_breakdown(skill_name)
    
    def get_available_skills(self) -> list[str]:
        """
        Get list of all available skills.
        """
        return self.skill_scorer.get_available_skills() 