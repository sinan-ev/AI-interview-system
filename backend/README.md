# AI Interview & Communication Assessment Platform — Backend

A production-ready, enterprise-grade backend for an **AI Interview & Communication Assessment Platform** built with **FastAPI**, **SQLAlchemy 2.0 (Async)**, **PostgreSQL (pgvector)**, **Celery**, and **Redis**.

---

## 🚀 Key Features

### 1. Multi-Modal Interview Modes
- **Normal Technical Interviews**: Standard software engineering technical interviews.
- **Topic-Specific Interviews**: Deep dives into Python, FastAPI, Machine Learning, System Design, etc.
- **Role-Based Interviews**: Software Engineer, Data Scientist, ML Engineer, DevOps, Backend Architect.
- **Company-Style Interviews**: Google, Amazon, Meta, Microsoft style problem framing and evaluation.
- **HR & Behavioral Interviews**: STAR methodology, leadership principles, conflict resolution.
- **Document / Resume RAG Interviews**: Upload candidate resumes or technical documents (PDF, DOCX, PPTX, TXT) to generate grounded questions via vector retrieval.
- **Voice-Based Interviews**: Candidate answers submitted via audio (WebM, WAV, MP3, OGG) with Whisper speech-to-text transcription.

### 2. Multi-Agent AI Assessment Pipeline
- **Question Generator Agent**: Synthesizes scenario-based questions with precise rubric criteria, concept checklists, and deduplication memory.
- **Answer Evaluator Agent**: Extracts factual claims, concept coverage, accuracy, and reasoning.
- **Communication Analyzer Agent**: Evaluates clarity, structure, grammatical correctness, and vocabulary.
- **Speech Signal Analyzer**: Computes speaking rate (WPM), filler word counts (`um`, `uh`, `like`), pause markers, and confidence estimation.
- **Interview Manager Agent**: Dynamic difficulty adjustment (adaptive branching based on rolling performance).

### 3. Deterministic & Explainable Scoring Engine
- **No Hallucinated Scores**: The LLM extracts qualitative evidence; scores are computed deterministically via mathematical weighting formulas.
- Clamped and normalized sub-scores for:
  - Technical: Correctness (40%), Concept Coverage (30%), Completeness (15%), Reasoning (15%)
  - Communication: Clarity (30%), Structure (25%), Grammar (25%), Fluency (20%)
  - Overall Weighted Answer Score: 70% Technical + 30% Communication

### 4. Background Workers & Celery Queue Architecture
- Asynchronous Celery tasks with Redis message broker:
  - `evaluate_answer_task` (evaluation queue)
  - `transcribe_audio_task` (transcription queue)
  - `ingest_document_task` (RAG ingestion queue)
  - `generate_feedback_task` (feedback generation queue)

---

## 🛠 Tech Stack

| Component | Technology |
|---|---|
| Framework | FastAPI (Python 3.12) |
| Database | PostgreSQL 16 + `pgvector` extension |
| Async ORM | SQLAlchemy 2.0 + asyncpg |
| Migrations | Alembic |
| Vector Embeddings | OpenAI `text-embedding-3-small` / Mock Provider (1536 dim) |
| LLM Provider | OpenAI GPT-4o / Structured Outputs / Mock Provider |
| Speech-to-Text | Whisper API / Mock Provider |
| Task Queue | Celery 5.x + Redis 7 |
| Validation | Pydantic v2 |
| Security | JWT (Access + Refresh tokens), Bcrypt password hashing |
| Testing | pytest + pytest-asyncio + pytest-cov (101 tests, 73% coverage) |

---

## 📁 Repository Structure

```
backend/
├── app/
│   ├── ai/
│   │   ├── agents/          # QuestionGenerator, AnswerEvaluator, InterviewManager, CommunicationAnalyzer
│   │   ├── embeddings/      # OpenAI & Mock embedding providers
│   │   ├── evaluation/      # Deterministic mathematical scoring engine
│   │   ├── llm/             # LLMProvider abstraction & Mock/OpenAI implementations
│   │   ├── prompts/         # Structured system & user prompts
│   │   └── workflows/       # Parallel EvaluationWorkflow, QuestionWorkflow
│   ├── api/
│   │   ├── v1/              # Auth, Users, Interviews, Questions, Answers, Documents, Speech, Feedback
│   │   └── router.py        # Central API router
│   ├── audio/               # Whisper STT & audio format validation
│   ├── core/                # Config, Database, Security, Exceptions, Logging, Dependencies
│   ├── models/              # SQLAlchemy models (User, Interview, Question, Answer, Evaluation, Document, etc.)
│   ├── rag/                 # DocumentProcessor (PDF/DOCX/PPTX/TXT), VectorStore, RAGService
│   ├── repositories/        # UserRepository, InterviewRepository, QuestionRepository, AnswerRepository
│   ├── schemas/             # Pydantic v2 schemas
│   ├── services/            # Business logic services
│   ├── utils/               # File uploads, path traversal prevention, audio sanitization
│   └── workers/             # Celery app & background tasks
├── migrations/              # Alembic migration scripts (001_initial_schema with pgvector)
├── scripts/                 # seed_db.py, start_dev.sh/.bat, run_worker.sh/.bat
├── tests/
│   ├── unit/                # Agents, scoring, audio, RAG, security, database, config, tasks
│   └── integration/         # Auth, interviews, questions, answers, speech, documents, feedback, users
├── Dockerfile               # Production multi-stage Docker build
├── docker-compose.yml       # Full stack: Postgres+pgvector, Redis, FastAPI, Celery worker
├── requirements.txt         # Pinned production dependencies
└── pytest.ini               # Pytest configuration
```

---

## ⚡ Quickstart

### 1. Run with Docker Compose (Recommended)

```bash
docker-compose up --build
```
This automatically starts:
- **PostgreSQL 16 with pgvector** on port `5432`
- **Redis 7** on port `6379`
- **FastAPI backend** on `http://localhost:8000` (auto-runs migrations and seeds database)
- **Celery worker** consuming background task queues

Swagger API documentation is immediately accessible at:
👉 **`http://localhost:8000/docs`**

---

### 2. Local Manual Setup

#### Step 1: Environment & Virtualenv
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

#### Step 2: Run Database Migrations & Seed
```bash
alembic upgrade head
python -m scripts.seed_db
```

#### Step 3: Start FastAPI Server
```bash
# Windows
scripts\start_dev.bat
# Or Linux/macOS
./scripts/start_dev.sh
```

#### Step 4: Start Celery Worker (In separate terminal)
```bash
# Windows
scripts\run_worker.bat
# Or Linux/macOS
./scripts/run_worker.sh
```

---

## 🧪 Testing & Verification

Run the complete test suite completely offline (no live databases or API keys required):

```bash
cd backend
pytest -v
```

Run test suite with coverage report:
```bash
pytest --cov=app --cov-report=term-missing
```

**Results:**
- **101 tests passed** (100% pass rate)
- **73% code coverage** across the entire backend

---

## 🛡 API Response Envelope

All API endpoints strictly conform to the unified envelope specification:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "message": "Operation completed successfully.",
  "request_id": "a4d34cb1-5374-4b55-a50e-b873e8f80456",
  "timestamp": "2026-10-09T12:00:00Z"
}
```
