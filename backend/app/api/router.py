"""
API Router Aggregator — v2 (complete).
Combines all v1 endpoint routers including documents, feedback, speech, and evaluation.
"""
from fastapi import APIRouter
from app.api.v1 import answers, auth, documents, feedback, health, interviews, questions, speech, users

api_router = APIRouter()

# Core health probes
api_router.include_router(health.router, prefix="", tags=["Health"])

# Auth & Users
api_router.include_router(auth.router)
api_router.include_router(users.router)

# Interviews & Questions
api_router.include_router(interviews.router)
api_router.include_router(questions.router)
api_router.include_router(answers.router)

# Documents & RAG
api_router.include_router(documents.router)

# Feedback, Analytics & Recommendations
api_router.include_router(feedback.router)

# Speech & Audio
api_router.include_router(speech.router)
