import json
import asyncio
import boto3
import requests
from datetime import datetime
from decimal import Decimal
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

def validate_participant_name(name):
    """Validate that participant name is provided and not empty"""
    if not name or not isinstance(name, str):
        return False, "participant_name must be a non-empty string"
    
    # Remove whitespace and check if empty
    if not name.strip():
        return False, "participant_name cannot be empty or only whitespace"
    
    # Check length (optional - you can adjust these limits)
    if len(name.strip()) < 2:
        return False, "participant_name must be at least 2 characters long"
    
    if len(name.strip()) > 100:
        return False, "participant_name cannot exceed 100 characters"
    
    return True, None

async def async_lambda_handler(event, context):
    try:
        # Parse the request body
        body = json.loads(event['body'])
        
        # Validate required fields including participant_name
        required_fields = ['time_elapsed', 'main_question_score', 'written_answers', 'participant_name']
        for field in required_fields:
            if field not in body:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': f'Missing required field: {field}'
                    })
                }
        
        # Extract instance_id if provided (optional for backward compatibility)
        instance_id = body.get('instance_id')
        
        # Extract and validate participant_name
        participant_name = body['participant_name']
        is_valid, error_message = validate_participant_name(participant_name)
        if not is_valid:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': error_message
                })
            }
        
        # Create assessment submission with participant_name
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
            ],
            participant_name=participant_name.strip()  # Use validated and cleaned name
        )
        
        # Run the async scoring function with skill-based scoring enabled and timeout
        try:
            # Set a timeout for the entire scoring process
            score = await asyncio.wait_for(
                scorer.calculate_total_score(submission, evaluator, use_skill_based_scoring=True),
                timeout=25.0  # 25 second timeout (leaving 5 seconds for Lambda overhead)
            )
        except asyncio.TimeoutError:
            return {
                'statusCode': 408,
                'body': json.dumps({
                    'error': 'Scoring process timed out. Please try again.'
                })
            }
        
        # Store the score in DynamoDB
        score_record = {
            'assessment_id': score.assessment_id,
            'timestamp': datetime.utcnow().isoformat(),
            'participant_name': submission.participant_name,  # Include participant_name in DynamoDB
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
        
        # Add instance_id to DynamoDB if provided
        if instance_id:
            score_record['instance_id'] = instance_id
        
        # Add skill-based scores to DynamoDB if available
        if score.skill_scores is not None:
            score_record['skill_scores'] = score.skill_scores
        if score.component_breakdown is not None:
            score_record['component_breakdown'] = score.component_breakdown
        
        # Add optional fields if provided
        if 'email' in body:
            score_record['email'] = body['email']
        if 'session_id' in body:
            score_record['session_id'] = body['session_id']
        
        # Convert all float values to Decimal for DynamoDB compatibility
        score_record = convert_floats_to_decimals(score_record)
        
        table.put_item(Item=score_record)
        
        # Send results to recruitment system webhook if instance_id is provided
        if instance_id and score.skill_scores is not None:
            try:
                notify_recruitment_system(instance_id, score.skill_scores, score_record)
            except Exception as webhook_error:
                print(f"Warning: Failed to send webhook to recruitment system: {webhook_error}")
                # Don't fail the assessment if webhook fails
        
        # Prepare response with both legacy and skill-based data
        response_body = {
            'assessment_id': score.assessment_id,
            'participant_name': submission.participant_name,  # Return name in response
            'total_score': score.total_score,
            'breakdown': score.breakdown
        }
        
        # Add skill-based scores to response if available
        if score.skill_scores is not None:
            response_body['skill_scores'] = score.skill_scores
        if score.component_breakdown is not None:
            response_body['component_breakdown'] = score.component_breakdown
        
        # Return response with participant_name for confirmation
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps(response_body)
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

def lambda_handler(event, context):
    """Wrapper to handle async Lambda function"""
    return asyncio.run(async_lambda_handler(event, context))

def notify_recruitment_system(instance_id: str, skill_scores: dict, score_record: dict):
    """
    Send assessment results to the recruitment system webhook.
    Maps skill scores to the expected format for the recruitment system.
    """
    try:
        # Map skill scores to the expected format
        technical_accuracy = skill_scores.get('technical_expertise', 0.0)
        problem_solving = skill_scores.get('problem_solving', 0.0)
        communication = skill_scores.get('communication', 0.0)
        
        # Prepare webhook payload
        webhook_payload = {
            'instance_id': instance_id,
            'technical_accuracy': float(technical_accuracy),
            'problem_solving': float(problem_solving),
            'communication': float(communication),
            'participant_name': score_record.get('participant_name', ''),
            'total_score': float(score_record.get('total_score', 0.0)),
            'time_elapsed': score_record.get('time_elapsed', 0)
        }
        
        # Send to recruitment system webhook
        webhook_url = "https://yourdomain.com/api/assessment/webhook"  # Update with your actual domain
        response = requests.post(
            webhook_url,
            json=webhook_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"Successfully sent webhook for instance {instance_id}")
        else:
            print(f"Webhook failed with status {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"Error sending webhook: {e}")
        raise

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