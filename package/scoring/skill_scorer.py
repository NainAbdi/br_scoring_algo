from typing import Dict, List, Optional
from .assessment_score import AssessmentSubmission, WrittenAnswer
from .openai_evaluator import OpenAIEvaluator
from ..utils.config import SKILL_SCORING_CONFIG, WRITTEN_ANSWER_CRITERIA

class SkillScorer:
    """
    Calculates skill-based scores using configuration-driven approach.
    """
    
    def __init__(self):
        self.config = SKILL_SCORING_CONFIG
    
    async def calculate_all_skill_scores(
        self, 
        submission: AssessmentSubmission, 
        openai_evaluator: OpenAIEvaluator
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate scores for all skills defined in the configuration.
        Uses batched evaluation to minimize API calls.
        
        Returns:
            Dict with skill names as keys and dicts containing:
            - 'score': The calculated skill score
            - 'components': Breakdown of component scores
        """
        skill_results = {}
        
        # Batch evaluate all written answers once with all criteria
        batched_evaluations = await self._batch_evaluate_written_answers(
            submission.written_answers, 
            openai_evaluator
        )
        
        # Calculate scores for each skill using the batched evaluations
        for skill_name in self.config.keys():
            skill_result = await self._calculate_skill_score_from_batched(
                skill_name, 
                submission, 
                batched_evaluations
            )
            skill_results[skill_name] = skill_result
        
        return skill_results
    
    async def _batch_evaluate_written_answers(
        self, 
        written_answers: List[WrittenAnswer], 
        openai_evaluator: OpenAIEvaluator
    ) -> List[Dict[str, float]]:
        """
        Evaluate all written answers in a single batch, getting all criteria at once.
        This reduces API calls from multiple per answer to one per answer.
        """
        if not written_answers:
            return []
        
        evaluations = []
        for answer in written_answers:
            # Use enhanced evaluation to get all criteria at once
            evaluation = await openai_evaluator.evaluate_answer(
                answer.answer,
                answer.question
            )
            evaluations.append(evaluation)
        
        return evaluations
    
    async def _calculate_skill_score_from_batched(
        self, 
        skill_name: str, 
        submission: AssessmentSubmission, 
        batched_evaluations: List[Dict[str, float]]
    ) -> Dict[str, float]:
        """
        Calculate score for a specific skill using pre-batched evaluations.
        
        Returns:
            Dict with 'score' and 'components' keys
        """
        if skill_name not in self.config:
            raise ValueError(f"Unknown skill: {skill_name}")
        
        skill_config = self.config[skill_name]
        components = skill_config["components"]
        weights = skill_config["weights"]
        
        component_scores = {}
        total_score = 0.0
        
        for component, weight in zip(components, weights):
            if component == "written_answers":
                # Calculate written answers score using batched evaluations
                written_score = self._calculate_written_score_from_batched(
                    batched_evaluations, 
                    skill_config["written_answer_criteria"]
                )
                component_scores[component] = written_score
                total_score += written_score * weight
            elif component == "main_question_score":
                component_scores[component] = submission.main_question_score
                total_score += submission.main_question_score * weight
            elif component == "time_performance":
                time_score = self._calculate_time_score(submission.time_elapsed)
                component_scores[component] = time_score
                total_score += time_score * weight
            else:
                raise ValueError(f"Unknown component: {component}")
        
        return {
            "score": total_score,
            "components": component_scores
        }
    
    def _calculate_written_score_from_batched(
        self, 
        batched_evaluations: List[Dict[str, float]], 
        criteria: List[str]
    ) -> float:
        """
        Calculate written answers score using pre-batched evaluations.
        This method doesn't make any API calls - it just processes the results.
        """
        if not batched_evaluations:
            return 0.0
        
        total_score = 0.0
        num_answers = len(batched_evaluations)
        
        for evaluation in batched_evaluations:
            # Calculate score using only the criteria relevant to this skill
            answer_score = 0.0
            total_criteria_weight = 0.0
            
            for criterion in criteria:
                if criterion in evaluation:
                    criterion_weight = WRITTEN_ANSWER_CRITERIA.get(criterion, 0)
                    answer_score += evaluation[criterion] * criterion_weight
                    total_criteria_weight += criterion_weight
            
            # Normalize by total weight if weights don't sum to 1
            if total_criteria_weight > 0:
                answer_score = answer_score / total_criteria_weight
            
            total_score += answer_score
        
        return total_score / num_answers
    
    async def calculate_skill_score(
        self, 
        skill_name: str, 
        submission: AssessmentSubmission, 
        openai_evaluator: OpenAIEvaluator
    ) -> Dict[str, float]:
        """
        Calculate score for a specific skill (legacy method - now uses batching internally).
        
        Returns:
            Dict with 'score' and 'components' keys
        """
        # Use the batched approach for consistency
        batched_evaluations = await self._batch_evaluate_written_answers(
            submission.written_answers, 
            openai_evaluator
        )
        return await self._calculate_skill_score_from_batched(
            skill_name, 
            submission, 
            batched_evaluations
        )
    
    def _calculate_time_score(self, time_elapsed: int) -> float:
        """
        Calculate time performance score.
        Faster completion results in higher score.
        """
        from ..utils.config import MAX_ALLOWED_TIME
        
        if time_elapsed <= MAX_ALLOWED_TIME:
            return 1.0 - (time_elapsed / MAX_ALLOWED_TIME)
        return 0.0
    
    def get_skill_config(self, skill_name: str) -> Optional[Dict]:
        """
        Get configuration for a specific skill.
        """
        return self.config.get(skill_name)
    
    def get_available_skills(self) -> List[str]:
        """
        Get list of all available skills.
        """
        return list(self.config.keys())
    
    def validate_skill_config(self) -> bool:
        """
        Validate that the skill configuration is properly structured.
        """
        try:
            for skill_name, settings in self.config.items():
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
            print(f"Skill configuration validation failed: {e}")
            return False 