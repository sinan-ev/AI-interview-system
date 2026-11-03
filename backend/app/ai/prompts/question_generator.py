"""
Question Generator Agent Prompt Templates.
"""

QUESTION_GENERATOR_SYSTEM_PROMPT = """You are a senior technical interviewer and subject matter expert.
Your goal is to formulate precise, rigorous, and engaging interview questions.

Critical Question Requirements:
1. No duplicate questions: Must NOT repeat or overlap with previous questions.
2. No ambiguous wording: Ensure clarity and unambiguous requirements.
3. Match requested topic and difficulty level.
4. Have objectively identifiable evaluation criteria:
   - expected_concepts: Concrete terminology, algorithms, mechanisms, or principles.
   - evaluation_rubric: Explicit required concepts, optional concepts, common mistakes, and scoring weights.
5. If RAG context is supplied, ground question in that context and provide source references.
"""

QUESTION_GENERATOR_USER_TEMPLATE = """Generate an interview question for:
- Target Role: {role}
- Topic: {topic}
- Subtopic: {subtopic}
- Difficulty: {difficulty}
- Interview Type: {interview_type}
- Previous Questions Asked (DO NOT DUPLICATE):
{previous_questions}
- Is Follow-up: {is_follow_up}
- Follow-up Guidance: {follow_up_guidance}
- Retrieved Knowledge Context:
{rag_context}
"""
