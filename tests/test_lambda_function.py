import os
import sys
import json
import asyncio
from dotenv import load_dotenv

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the lambda handler
from package.lambda_function import lambda_handler

# Load environment variables from .env file
load_dotenv()

def test_lambda_function():
    # Test event data (your provided data)
    test_event = {
        "body": "{\"time_elapsed\": 300, \"main_question_score\": 0.8, \"written_answers\": [{\"question_id\": \"q1\", \"question\": \"What is the capital of France?\", \"answer\": \"Paris is the capital of France. It is known for its iconic Eiffel Tower and rich cultural heritage.\"}]}"
    }
    
    # Mock context (not used in our handler)
    context = {}
    
    print("Testing Lambda Function with your data...")
    print(f"Input: {test_event['body']}")
    print("\n" + "="*50)
    
    try:
        # Call the lambda handler
        response = lambda_handler(test_event, context)
        
        print(f"Status Code: {response['statusCode']}")
        print(f"Headers: {response['headers']}")
        print(f"Response Body: {response['body']}")
        
        # Parse and pretty print the response
        if response['statusCode'] == 200:
            response_data = json.loads(response['body'])
            print("\n" + "="*50)
            print("PARSED RESPONSE:")
            print(f"Total Score: {response_data['total_score']}")
            print(f"Breakdown: {json.dumps(response_data['breakdown'], indent=2)}")
        else:
            print(f"\nError Response: {response['body']}")
            
    except Exception as e:
        print(f"Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lambda_function() 