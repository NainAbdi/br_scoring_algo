# At the very top of example.py, add these two lines:
import asyncio
from dotenv import load_dotenv  # Add this import
load_dotenv()  # Add this line to load the .env file

# Then the rest of your imports
from src.scoring.assessment_score import AssessmentSubmission, WrittenAnswer
from src.scoring.scoring_algorithm import ScoringAlgorithm
from src.scoring.gemini_evaluator import GeminiEvaluator

async def main():
    # Create a sample assessment submission
    submission = AssessmentSubmission(
        time_taken=1800,  # 30 minutes
        main_question_correct=True,
        written_answers=[
            WrittenAnswer(
                question_id="q1",
                answer_text="The purpose of version control is to track changes in code over time, "
                          "enable collaboration between developers, and maintain a history of "
                          "modifications. It helps teams work together efficiently and provides "
                          "a safety net for code changes.",
                question_context="What is the purpose of version control?"
            ),
            WrittenAnswer(
                question_id="q2",
                answer_text="API stands for Application Programming Interface. It's a set of rules "
                          "and protocols that allows different software applications to communicate "
                          "with each other. APIs define the methods and data formats that "
                          "applications can use to request and exchange information.",
                question_context="What is an API and what is its purpose?"
            )
        ]
    )

    # Initialize the scoring system
    scorer = ScoringAlgorithm()
    evaluator = GeminiEvaluator()

    try:
        # Calculate the score
        score = await scorer.calculate_total_score(submission, evaluator)
        
        # Print the results
        print("\nAssessment Score Results:")
        print("-" * 50)
        print(f"Total Score: {score.total_score:.2%}")
        print("\nScore Breakdown:")
        print(f"Time Score: {score.breakdown['time_score']:.2%}")
        print(f"Main Question Score: {score.breakdown['main_question_score']:.2%}")
        print(f"Written Answers Score: {score.breakdown['written_answers_score']:.2%}")
        
    except Exception as e:
        print(f"Error calculating score: {str(e)}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 