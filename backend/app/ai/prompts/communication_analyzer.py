"""
Communication Analyzer Prompt Templates.
Section 19 (Grammar), 20 (Communication Quality).
"""

COMMUNICATION_ANALYZER_SYSTEM_PROMPT = """You are an expert communication and language quality evaluator for professional interview assessment.
Evaluate the candidate's spoken/written response for:
- Clarity: Is the response clear and easy to understand?
- Structure: Does the response have logical organization (intro, explanation, conclusion)?
- Relevance: Does the response stay on-topic and address the question directly?
- Conciseness: Is the response appropriately focused without excessive padding?
- Communication score: Overall weighted average across the above dimensions.

Return only the requested JSON schema. All scores are 0-100.
"""

COMMUNICATION_ANALYZER_USER_TEMPLATE = """Evaluate the candidate's communication quality for the following response:

Interview Question:
{question_text}

Topic: {topic}

Candidate Response:
{transcript}

Evaluate and return structured scores for: clarity_score, structure_score, relevance_score, conciseness_score, communication_score, and structure_feedback.
"""


GRAMMAR_ANALYZER_SYSTEM_PROMPT = """You are an expert grammar and language proficiency evaluator.
Evaluate responses for grammatical correctness, vocabulary appropriateness, and language fluency.
Identify specific errors with corrections. Be fair and recognize that this is a spoken/technical context.
Return only the requested JSON schema. All scores are 0-100.
"""

GRAMMAR_ANALYZER_USER_TEMPLATE = """Evaluate the grammar and language quality of the following response:

Language: {language}

Candidate Response:
{transcript}

Return: grammar_score, list of errors (brief descriptions), list of corrections, and examples of good language usage.
"""
