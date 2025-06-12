import os
import asyncio
from dotenv import load_dotenv
from src.scoring.gemini_evaluator import GeminiEvaluator
from src.utils.config import GEMINI_MODEL_NAME

# Load environment variables from .env file
load_dotenv()

async def test_evaluation():
    # Initialize the evaluator
    evaluator = GeminiEvaluator()
    
    print(f"\nUsing model: {GEMINI_MODEL_NAME}")
    
    # Test case 1: Simple technical answer
    test_answer = """
    Python is a high-level, interpreted programming language known for its readability and simplicity.
    It supports multiple programming paradigms including procedural, object-oriented, and functional programming.
    Python uses dynamic typing and garbage collection.
    """
    
    test_context = "Explain what Python is as a programming language."
    
    try:
        print("\nTesting evaluation with REST API...")
        result = await evaluator.evaluate_answer(test_answer, test_context)
        print("\nEvaluation Results:")
        print(f"Technical Accuracy: {result['technical_accuracy']}")
        print(f"Clarity: {result['clarity']}")
        print(f"Total Score: {result['total_score']}")
        print("\nTest completed successfully!")
    except Exception as e:
        print(f"\nError during evaluation: {str(e)}")

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_evaluation()) 