import os
from typing import Dict
import google.generativeai as genai
from ..utils.config import GEMINI_MODEL_NAME, WRITTEN_ANSWER_CRITERIA

class GeminiEvaluator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not found. Please set GEMINI_API_KEY environment variable.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    
    async def evaluate_answer(
        self, 
        answer_text: str, 
        question_context: str = ""
    ) -> Dict[str, float]:
        """
        Evaluate a written answer using Gemini API.
        Returns scores for technical accuracy and clarity.
        """
        prompt = self._create_evaluation_prompt(answer_text, question_context)
        
        try:
            response = self.model.generate_content(prompt)
            evaluation = self._parse_evaluation(response.text)
            return evaluation
        except Exception as e:
            raise Exception(f"Failed to evaluate answer: {str(e)}")
    
    def _create_evaluation_prompt(self, answer_text: str, question_context: str) -> str:
        return f"""
        Evaluate the following answer based on technical accuracy and clarity.
        
        Question Context: {question_context}
        
        Answer: {answer_text}
        
        Please provide scores from 0 to 1 for:
        1. Technical Accuracy: How technically correct is the answer?
        2. Clarity: How clear and well-explained is the answer?
        
        Format your response as:
        Technical Accuracy: [score]
        Clarity: [score]
        """
    
    def _parse_evaluation(self, response_text: str) -> Dict[str, float]:
        """
        Parse the Gemini API response into structured scores.
        """
        try:
            lines = response_text.strip().split('\n')
            scores = {}
            
            for line in lines:
                if ':' in line:
                    criterion, score = line.split(':')
                    criterion = criterion.strip().lower()
                    score = float(score.strip())
                    scores[criterion] = score
            
            # Calculate total score based on weights
            total_score = sum(
                scores.get(criterion, 0) * weight 
                for criterion, weight in WRITTEN_ANSWER_CRITERIA.items()
            )
            
            return {
                "technical_accuracy": scores.get("technical accuracy", 0),
                "clarity": scores.get("clarity", 0),
                "total_score": total_score
            }
        except Exception as e:
            raise Exception(f"Failed to parse evaluation response: {str(e)}") 