from typing import Dict
from .assessment_score import AssessmentSubmission, AssessmentScore, WrittenAnswer
from .gemini_evaluator import GeminiEvaluator
from ..utils.config import SCORING_WEIGHTS, MAX_ALLOWED_TIME

class ScoringAlgorithm:
    def __init__(self):
        self.time_weight = SCORING_WEIGHTS["time"]
        self.main_question_weight = SCORING_WEIGHTS["main_question"]
        self.written_answers_weight = SCORING_WEIGHTS["written_answers"]
        self.max_allowed_time = MAX_ALLOWED_TIME
    
    async def calculate_total_score(
        self, 
        submission: AssessmentSubmission, 
        gemini_evaluator: GeminiEvaluator
    ) -> AssessmentScore:
        """
        Calculate the total score for an assessment submission.
        """
        # Calculate time score
        time_score = self._calculate_time_score(submission.time_elapsed)
        
        # Calculate main question score (now using the float value directly)
        main_question_score = submission.main_question_score
        
        # Calculate written answers score
        written_answers_score = await self._evaluate_written_answers(
            submission.written_answers, 
            gemini_evaluator
        )
        
        # Calculate final score
        total_score = (
            (time_score * self.time_weight) +
            (main_question_score * self.main_question_weight) +
            (written_answers_score * self.written_answers_weight)
        )
        
        return AssessmentScore(
            total_score=total_score,
            breakdown={
                "time_score": time_score,
                "main_question_score": main_question_score,
                "written_answers_score": written_answers_score
            }
        )
    
    def _calculate_time_score(self, time_elapsed: int) -> float:
        """
        Calculate score based on time taken.
        Faster completion results in higher score.
        """
        if time_elapsed <= self.max_allowed_time:
            return 1.0 - (time_elapsed / self.max_allowed_time)
        return 0.0
    
    async def _evaluate_written_answers(
        self, 
        answers: list[WrittenAnswer], 
        gemini_evaluator: GeminiEvaluator
    ) -> float:
        """
        Evaluate all written answers and return average score.
        """
        if not answers:
            return 0.0
        
        total_score = 0
        for answer in answers:
            evaluation = await gemini_evaluator.evaluate_answer(
                answer.answer,
                answer.question
            )
            total_score += evaluation["total_score"]
        
        return total_score / len(answers) 