# Assessment Scoring Algorithm

A Python-based scoring system for assessments that evaluates:
- Time taken to complete the assessment
- Correctness of the main question
- Quality of written answers (using Gemini AI)

## Features

- Configurable scoring weights
- AI-powered evaluation of written answers
- Detailed score breakdowns
- Type-safe implementation
- Async support for API calls

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
Create a `.env` file with:
```
GEMINI_API_KEY=your_api_key_here
```

## Usage

```python
from src.scoring.assessment_score import AssessmentSubmission, WrittenAnswer
from src.scoring.scoring_algorithm import ScoringAlgorithm
from src.scoring.gemini_evaluator import GeminiEvaluator

# Create an assessment submission
submission = AssessmentSubmission(
    time_taken=1800,  # 30 minutes
    main_question_correct=True,
    written_answers=[
        WrittenAnswer(
            question_id="q1",
            answer_text="The candidate's response...",
            question_context="What is the purpose of X?"
        )
    ]
)

# Initialize the scoring system
scorer = ScoringAlgorithm()
evaluator = GeminiEvaluator()

# Calculate the score
score = await scorer.calculate_total_score(submission, evaluator)
print(score.to_dict())
```

## Project Structure

```
br_scoring_algo/
├── src/
│   ├── scoring/
│   │   ├── assessment_score.py    # Data models
│   │   ├── scoring_algorithm.py   # Main scoring logic
│   │   └── gemini_evaluator.py    # AI evaluation
│   └── utils/
│       └── config.py             # Configuration
└── tests/                        # Test files
```

## Scoring Weights

- Time: 20%
- Main Question: 30%
- Written Answers: 50%

Written answers are evaluated on:
- Technical Accuracy: 60%
- Clarity: 40%
