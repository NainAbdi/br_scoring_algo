import os
import json
from typing import Dict
import requests
from ..utils.config import GEMINI_MODEL_NAME, WRITTEN_ANSWER_CRITERIA

class GeminiEvaluator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not found. Please set GEMINI_API_KEY environment variable.")
        
        # Configure API endpoint and headers
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL_NAME}:generateContent"
        self.headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
    
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
            # Prepare the request payload
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.2,  # Lower temperature for more consistent scoring
                    "topP": 0.8,
                    "topK": 40
                }
            }
            
            # Make the API request
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()  # Raise exception for bad status codes
            
            # Parse the response
            result = response.json()
            if "candidates" not in result or not result["candidates"]:
                raise Exception("No response from Gemini API")
                
            evaluation_text = result["candidates"][0]["content"]["parts"][0]["text"]
            evaluation = self._parse_evaluation(evaluation_text)
            return evaluation
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse API response: {str(e)}")
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
                    try:
                        score = float(score.strip())
                        scores[criterion] = score
                    except ValueError:
                        continue  # Skip lines that don't have valid scores
            
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