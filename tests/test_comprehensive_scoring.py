import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scoring.gemini_evaluator import GeminiEvaluator
from src.utils.config import GEMINI_MODEL_NAME

# Load environment variables from .env file
load_dotenv()

async def test_comprehensive_scoring():
    # Initialize the evaluator
    evaluator = GeminiEvaluator()
    
    print(f"\n{'='*60}")
    print("COMPREHENSIVE SCORING TEST")
    print(f"{'='*60}")
    print(f"Using model: {GEMINI_MODEL_NAME}")
    
    # Test cases with more dramatic quality differences
    test_cases = [
        {
            "name": "VERY BAD ANSWER",
            "question": "Explain the concept of recursion in programming.",
            "answer": "Recursion is when you call a function. It's like a loop.",
            "expected_score_range": (0.1, 0.4)
        },
        {
            "name": "BAD ANSWER",
            "question": "Explain the concept of recursion in programming.",
            "answer": "Recursion is when a function calls itself. You need a base case to stop it. It's useful for some problems.",
            "expected_score_range": (0.3, 0.6)
        },
        {
            "name": "MEDIUM ANSWER", 
            "question": "Explain the concept of recursion in programming.",
            "answer": "Recursion is a programming technique where a function calls itself to solve a problem. It has two main parts: a base case that stops the recursion and a recursive case that calls the function with a smaller input. For example, when calculating factorial, n! = n * (n-1)! and the base case is 0! = 1. This approach is useful for problems that can be broken down into smaller, similar subproblems.",
            "expected_score_range": (0.6, 0.8)
        },
        {
            "name": "GOOD ANSWER",
            "question": "Explain the concept of recursion in programming.",
            "answer": "Recursion is a powerful programming technique where a function calls itself to solve a problem by breaking it down into smaller, similar subproblems. It consists of two essential components: a base case that stops the recursion and a recursive case that calls the function with a smaller input. For example, calculating factorial: n! = n * (n-1)! with base case 0! = 1. This approach is particularly elegant for problems that can be naturally divided into similar subproblems, such as tree traversal and sorting algorithms like merge sort.",
            "expected_score_range": (0.8, 0.95)
        },
        {
            "name": "EXCELLENT ANSWER",
            "question": "Explain the concept of recursion in programming with examples and applications.",
            "answer": "Recursion is a fundamental programming paradigm where a function calls itself to solve a problem by breaking it down into smaller, similar subproblems. It consists of two essential components: a base case that stops the recursion and a recursive case that calls the function with a smaller input. For example, calculating factorial: n! = n * (n-1)! with base case 0! = 1. This approach is particularly elegant for problems that can be naturally divided into similar subproblems, such as tree traversal (in-order, pre-order, post-order), sorting algorithms like merge sort and quick sort, and mathematical computations like Fibonacci sequences. The key insight is that each recursive call works on a smaller version of the original problem until it reaches the base case. Recursion is especially powerful for problems involving hierarchical data structures, divide-and-conquer algorithms, and mathematical induction.",
            "expected_score_range": (0.9, 1.0)
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"Question: {test_case['question']}")
        print(f"Answer: {test_case['answer'][:100]}{'...' if len(test_case['answer']) > 100 else ''}")
        
        try:
            result = await evaluator.evaluate_answer(test_case['answer'], test_case['question'])
            
            technical_accuracy = result['technical_accuracy']
            clarity = result['clarity']
            total_score = result['total_score']
            
            print(f"Technical Accuracy: {technical_accuracy:.3f}")
            print(f"Clarity: {clarity:.3f}")
            print(f"Total Score: {total_score:.3f}")
            
            # Check if score is in expected range
            min_expected, max_expected = test_case['expected_score_range']
            if min_expected <= total_score <= max_expected:
                print(f"✅ Score is in expected range ({min_expected:.1f}-{max_expected:.1f})")
            else:
                print(f"❌ Score is outside expected range ({min_expected:.1f}-{max_expected:.1f})")
            
            results.append({
                "name": test_case['name'],
                "total_score": total_score,
                "technical_accuracy": technical_accuracy,
                "clarity": clarity,
                "in_range": min_expected <= total_score <= max_expected
            })
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                "name": test_case['name'],
                "error": str(e)
            })
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    successful_tests = [r for r in results if 'error' not in r]
    failed_tests = [r for r in results if 'error' in r]
    
    print(f"Successful tests: {len(successful_tests)}/{len(results)}")
    print(f"Failed tests: {len(failed_tests)}/{len(results)}")
    
    if successful_tests:
        print(f"\nScore progression (should increase):")
        for result in successful_tests:
            print(f"  {result['name']}: {result['total_score']:.3f}")
        
        # Check if scores are properly differentiated
        scores = [r['total_score'] for r in successful_tests]
        if len(scores) >= 2:
            score_differences = [scores[i+1] - scores[i] for i in range(len(scores)-1)]
            positive_differences = [d for d in score_differences if d > 0]
            
            if len(positive_differences) == len(score_differences):
                print(f"\n✅ Score differentiation: GOOD - Each answer type scores higher than the previous")
            else:
                print(f"\n❌ Score differentiation: NEEDS IMPROVEMENT - Some answers don't follow expected progression")
    
    if failed_tests:
        print(f"\nFailed tests:")
        for result in failed_tests:
            print(f"  {result['name']}: {result['error']}")
    
    print(f"\n{'='*60}")
    print("TEST COMPLETED")
    print(f"{'='*60}")

if __name__ == "__main__":
    # Run the comprehensive test
    asyncio.run(test_comprehensive_scoring()) 