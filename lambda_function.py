import json
import asyncio
from src.scoring.assessment_score import AssessmentSubmission, WrittenAnswer
from src.scoring.scoring_algorithm import ScoringAlgorithm
from src.scoring.gemini_evaluator import GeminiEvaluator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize scoring components
scorer = ScoringAlgorithm()
evaluator = GeminiEvaluator()

def lambda_handler(event, context):
    try:
        # Parse the request body
        body = json.loads(event['body'])
        
        # Validate required fields
        required_fields = ['time_elapsed', 'main_question_score', 'written_answers']
        for field in required_fields:
            if field not in body:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': f'Missing required field: {field}'
                    })
                }
        
        # Create assessment submission
        submission = AssessmentSubmission(
            time_elapsed=body['time_elapsed'],
            main_question_score=body['main_question_score'],
            written_answers=[
                WrittenAnswer(
                    question_id=answer['question_id'],
                    question=answer['question'],
                    answer=answer['answer']
                )
                for answer in body['written_answers']
            ]
        )
        
        # Run the async scoring function
        score = asyncio.run(scorer.calculate_total_score(submission, evaluator))
        
        # Return response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',  # Enable CORS
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'total_score': score.total_score,
                'breakdown': score.breakdown
            })
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Invalid JSON in request body'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

# Handle OPTIONS requests for CORS
def options_handler(event, context):
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': ''
    } 