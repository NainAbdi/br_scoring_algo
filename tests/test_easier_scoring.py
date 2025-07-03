import os
import sys
import json
import asyncio
from dotenv import load_dotenv

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scoring.gemini_evaluator import GeminiEvaluator

# Load environment variables from .env file
load_dotenv()

async def test_easier_scoring():
    test_answer = "Paris is the capital of France. It is known for its iconic Eiffel Tower and rich cultural heritage."
    test_context = "What is the capital of France?"
    
    print("Testing easier scoring prompt...")
    print(f"Test Answer: {test_answer}")
    print("\n" + "="*60)
    
    try:
        # Test with current prompt
        print("Testing with CURRENT prompt:")
        evaluator = GeminiEvaluator()
        result = await evaluator.evaluate_answer(test_answer, test_context)
        print(f"   Technical Accuracy: {result['technical_accuracy']}")
        print(f"   Clarity: {result['clarity']}")
        print(f"   Total Score: {result['total_score']}")
        
        print("\n" + "="*60)
        print("The current prompt is still the strict one.")
        print("To see the easier scoring, we need to update the prompt in the code.")
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_easier_scoring()) 