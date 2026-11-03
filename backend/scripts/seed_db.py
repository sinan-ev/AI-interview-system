"""
Database Seeding Script.
Populates standard interview topics, skills taxonomy, and an initial admin account.
Run with: python -m scripts.seed_db
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from app.core.database import async_session_factory
from app.core.security import get_password_hash
from app.models.user import User
from app.models.skill import Skill
from app.core.logging import logger

CORE_SKILLS = [
    # Technical: Programming Languages
    {"name": "Python", "category": "technical", "description": "Core Python programming, OOP, generators, decorators, GIL, memory model"},
    {"name": "JavaScript", "category": "technical", "description": "ES6+, event loop, closures, promises, async/await, DOM"},
    {"name": "TypeScript", "category": "technical", "description": "Static typing, generics, interfaces, advanced type utilities"},
    {"name": "Go", "category": "technical", "description": "Goroutines, channels, interfaces, memory allocation, profiling"},
    {"name": "Java", "category": "technical", "description": "JVM, memory model, multithreading, collections framework"},

    # Technical: Frameworks & Backend
    {"name": "FastAPI", "category": "technical", "description": "Async API design, Pydantic, dependency injection, OpenAPI"},
    {"name": "Django", "category": "technical", "description": "ORM, middleware, auth, DRF, caching, celery"},
    {"name": "Node.js", "category": "technical", "description": "Event loop, streams, Express/Nest, worker threads"},

    # Technical: Databases & Distributed Systems
    {"name": "PostgreSQL", "category": "technical", "description": "Query optimization, indexing, ACID transactions, pgvector"},
    {"name": "Redis", "category": "technical", "description": "In-memory caching, pub/sub, Lua scripting, rate limiting"},
    {"name": "System Design", "category": "technical", "description": "Scalability, microservices, load balancing, consensus, CAP theorem"},
    {"name": "Data Structures & Algorithms", "category": "technical", "description": "Complexity, trees, graphs, dynamic programming, sorting"},

    # Technical: AI / ML / Data Science
    {"name": "Machine Learning", "category": "technical", "description": "Supervised/unsupervised learning, metrics, feature engineering"},
    {"name": "Deep Learning", "category": "technical", "description": "Neural networks, backprop, transformers, embeddings, LLMs"},
    {"name": "NLP & LLM", "category": "technical", "description": "Tokenization, attention mechanism, RAG, prompt engineering, fine-tuning"},

    # Soft Skills
    {"name": "Communication", "category": "soft_skill", "description": "Clarity of thought, articulation, conciseness, structured explanation"},
    {"name": "Problem Solving", "category": "soft_skill", "description": "First-principles thinking, analytical reasoning, edge-case analysis"},
    {"name": "Behavioral & Leadership", "category": "soft_skill", "description": "STAR method, conflict resolution, ownership, mentorship"},
]


async def seed():
    logger.info("Starting database seeding...")
    async with async_session_factory() as db:
        # 1. Seed Core Skills
        for skill_data in CORE_SKILLS:
            result = await db.execute(select(Skill).where(Skill.name == skill_data["name"]))
            existing = result.scalar_one_or_none()
            if not existing:
                skill = Skill(**skill_data)
                db.add(skill)
                logger.info(f"Added skill: {skill_data['name']}")
            else:
                logger.info(f"Skill already exists: {skill_data['name']}")

        # 2. Seed Default Admin User
        admin_email = "admin@ai-interview.local"
        res = await db.execute(select(User).where(User.email == admin_email))
        existing_admin = res.scalar_one_or_none()
        if not existing_admin:
            admin_user = User(
                name="System Administrator",
                email=admin_email,
                password_hash=get_password_hash("AdminSecret2026!"),
                role="admin",
                is_active=True,
            )
            db.add(admin_user)
            logger.info(f"Created default admin user: {admin_email}")
        else:
            logger.info(f"Admin user already exists: {admin_email}")

        await db.commit()
    logger.info("Database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
