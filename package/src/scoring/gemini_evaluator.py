import os
import json
from typing import Dict
import requests
from utils.config import GEMINI_MODEL_NAME, WRITTEN_ANSWER_CRITERIA, LEGACY_WRITTEN_ANSWER_CRITERIA

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
        question_context: str = "",
        use_legacy_criteria: bool = False
    ) -> Dict[str, float]:
        """
        Evaluate a written answer using Gemini API.
        Returns scores for all criteria or legacy criteria based on parameter.
        """
        if use_legacy_criteria:
            return await self._evaluate_legacy(answer_text, question_context)
        else:
            return await self._evaluate_enhanced(answer_text, question_context)
    
    async def _evaluate_enhanced(
        self, 
        answer_text: str, 
        question_context: str
    ) -> Dict[str, float]:
        """
        Enhanced evaluation using all criteria for skill-based scoring.
        """
        prompt = self._create_enhanced_evaluation_prompt(answer_text, question_context)
        
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
            evaluation = self._parse_enhanced_evaluation(evaluation_text)
            return evaluation
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse API response: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to evaluate answer: {str(e)}")
    
    async def _evaluate_legacy(
        self, 
        answer_text: str, 
        question_context: str
    ) -> Dict[str, float]:
        """
        Legacy evaluation using only technical accuracy and clarity.
        """
        prompt = self._create_legacy_evaluation_prompt(answer_text, question_context)
        
        try:
            # Prepare the request payload
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.2,
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
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            if "candidates" not in result or not result["candidates"]:
                raise Exception("No response from Gemini API")
                
            evaluation_text = result["candidates"][0]["content"]["parts"][0]["text"]
            evaluation = self._parse_legacy_evaluation(evaluation_text)
            return evaluation
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse API response: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to evaluate answer: {str(e)}")
    
    def _create_enhanced_evaluation_prompt(self, answer_text: str, question_context: str) -> str:
        return f"""
        Evaluate the following answer based on multiple criteria for a comprehensive assessment.
        
        Question Context: {question_context}
        
        Answer: {answer_text}
        
        Please provide scores from 0 to 1 for each of the following criteria:
        
        1. Technical Accuracy: How technically correct and accurate is the answer? Does it demonstrate proper knowledge and understanding?
        
        2. Problem Solving Methodology: How well does the candidate approach and solve the problem? Do they use logical steps, consider alternatives, and show systematic thinking?
        
        3. Logical Thinking: How clear and logical is the reasoning? Is the argument well-structured and does it follow a coherent thought process?
        
        4. Clarity: How clear and understandable is the explanation? Can someone easily follow their reasoning and conclusions?
        
        5. Presentation: How well is the answer organized and presented? Is it well-structured, professional, and easy to read?
        
        Be strict and fair in your evaluation:
        - Only give a score above 0.8 for answers that are truly excellent in that specific criterion
        - Give a score below 0.5 for answers that are poor or missing key elements in that criterion
        - Most average answers should score between 0.5 and 0.7 for each criterion
        - Use the full range from 0 to 1 as appropriate for each criterion
        - Evaluate each criterion independently
        
        Format your response exactly as:
        Technical Accuracy: [score]
        Problem Solving Methodology: [score]
        Logical Thinking: [score]
        Clarity: [score]
        Presentation: [score]
        """
    
    def _create_legacy_evaluation_prompt(self, answer_text: str, question_context: str) -> str:
        return f"""
        Evaluate the following answer based on technical accuracy and clarity.
        
        Question Context: {question_context}
        
        Answer: {answer_text}
        
        Please provide scores from 0 to 1 for:
        1. Technical Accuracy: How technically correct is the answer?
        2. Clarity: How clear and well-explained is the answer?
        
        Be strict and fair in your evaluation:
        - Only give a score above 0.8 for answers that are truly excellent, comprehensive, and correct.
        - Give a score below 0.5 for answers that are incomplete, vague, or have any significant errors.
        - Most average answers should score between 0.5 and 0.7.
        - Do not be generous with high scores, but if the answer is truly outstanding, it is okay to give a high score.
        - Use the full range from 0 to 1 as appropriate.
        
        Format your response as:
        Technical Accuracy: [score]
        Clarity: [score]
        """
    
    def _parse_enhanced_evaluation(self, response_text: str) -> Dict[str, float]:
        """
        Parse the enhanced Gemini API response into structured scores.
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
                "problem_solving_methodology": scores.get("problem solving methodology", 0),
                "logical_thinking": scores.get("logical thinking", 0),
                "clarity": scores.get("clarity", 0),
                "presentation": scores.get("presentation", 0),
                "total_score": total_score
            }
        except Exception as e:
            raise Exception(f"Failed to parse evaluation response: {str(e)}")
    
    def _parse_legacy_evaluation(self, response_text: str) -> Dict[str, float]:
        """
        Parse the legacy Gemini API response into structured scores.
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
            
            # Calculate total score based on legacy weights
            total_score = sum(
                scores.get(criterion, 0) * weight 
                for criterion, weight in LEGACY_WRITTEN_ANSWER_CRITERIA.items()
            )
            
            return {
                "technical_accuracy": scores.get("technical accuracy", 0),
                "clarity": scores.get("clarity", 0),
                "total_score": total_score
            }
        except Exception as e:
            raise Exception(f"Failed to parse evaluation response: {str(e)}") 