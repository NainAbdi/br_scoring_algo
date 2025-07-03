from decimal import Decimal
import json
import asyncio
import boto3
from datetime import datetime
from src.scoring.assessment_score import AssessmentSubmission, WrittenAnswer
from src.scoring.scoring_algorithm import ScoringAlgorithm
from src.scoring.gemini_evaluator import GeminiEvaluator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize scoring components
scorer = ScoringAlgorithm()
evaluator = GeminiEvaluator()

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('br_assessment_scores')

def convert_floats_to_decimals(obj):
    """Recursively convert float values to Decimal for DynamoDB compatibility"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {key: convert_floats_to_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimals(item) for item in obj]
    else:
        return obj

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
        
        # Store the score in DynamoDB
        score_record = {
            'assessment_id': score.assessment_id,
            'timestamp': datetime.utcnow().isoformat(),
            'total_score': score.total_score,
            'time_score': score.breakdown['time_score'],
            'main_question_score': score.breakdown['main_question_score'],
            'written_answers_score': score.breakdown['written_answers_score'],
            'time_elapsed': submission.time_elapsed,
            'main_question_score_input': submission.main_question_score,
            'written_answers': [
                {
                    'question_id': answer.question_id,
                    'question': answer.question,
                    'answer': answer.answer
                }
                for answer in submission.written_answers
            ]
        }
        
        # Add optional fields if provided
        if 'name' in body:
            score_record['name'] = body['name']
        if 'email' in body:
            score_record['email'] = body['email']
        if 'session_id' in body:
            score_record['session_id'] = body['session_id']
        
        # Convert all float values to Decimal for DynamoDB compatibility
        score_record = convert_floats_to_decimals(score_record)
        
        table.put_item(Item=score_record)
        
        # Return response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'assessment_id': score.assessment_id,
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
