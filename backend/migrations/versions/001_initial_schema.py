"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. Enable pgvector extension if PostgreSQL
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. refresh_tokens
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)

    # 3. skills
    op.create_table(
        'skills',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_skill_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['parent_skill_id'], ['skills.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_skills_name'), 'skills', ['name'], unique=True)

    # 4. user_skills
    op.create_table(
        'user_skills',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('skill_id', sa.String(length=36), nullable=False),
        sa.Column('proficiency_score', sa.Float(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('evidence_count', sa.Integer(), nullable=False),
        sa.Column('last_assessed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'skill_id', name='uq_user_skill')
    )
    op.create_index(op.f('ix_user_skills_user_id'), 'user_skills', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_skills_skill_id'), 'user_skills', ['skill_id'], unique=False)

    # 5. interviews
    op.create_table(
        'interviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=100), nullable=False),
        sa.Column('interview_type', sa.String(length=50), nullable=False),
        sa.Column('difficulty', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('total_questions', sa.Integer(), nullable=False),
        sa.Column('current_question', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('configuration', sa.JSON(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interviews_status'), 'interviews', ['status'], unique=False)
    op.create_index(op.f('ix_interviews_user_id'), 'interviews', ['user_id'], unique=False)

    # 6. interview_questions
    op.create_table(
        'interview_questions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('interview_id', sa.String(length=36), nullable=False),
        sa.Column('question_number', sa.Integer(), nullable=False),
        sa.Column('topic', sa.String(length=100), nullable=False),
        sa.Column('subtopic', sa.String(length=100), nullable=True),
        sa.Column('difficulty', sa.String(length=50), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('expected_concepts', sa.JSON(), nullable=False),
        sa.Column('evaluation_rubric', sa.JSON(), nullable=False),
        sa.Column('source_document_ids', sa.JSON(), nullable=False),
        sa.Column('parent_question_id', sa.String(length=36), nullable=True),
        sa.Column('is_follow_up', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_question_id'], ['interview_questions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_questions_interview_id'), 'interview_questions', ['interview_id'], unique=False)
    op.create_index(op.f('ix_interview_questions_topic'), 'interview_questions', ['topic'], unique=False)

    # 7. answers
    op.create_table(
        'answers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('question_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('text_answer', sa.Text(), nullable=True),
        sa.Column('audio_file_url', sa.String(length=500), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['interview_questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_answers_question_id'), 'answers', ['question_id'], unique=False)
    op.create_index(op.f('ix_answers_user_id'), 'answers', ['user_id'], unique=False)

    # 8. evaluations
    op.create_table(
        'evaluations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('answer_id', sa.String(length=36), nullable=False),
        sa.Column('technical_score', sa.Float(), nullable=False),
        sa.Column('accuracy_score', sa.Float(), nullable=False),
        sa.Column('completeness_score', sa.Float(), nullable=False),
        sa.Column('reasoning_score', sa.Float(), nullable=False),
        sa.Column('grammar_score', sa.Float(), nullable=False),
        sa.Column('communication_score', sa.Float(), nullable=False),
        sa.Column('fluency_score', sa.Float(), nullable=False),
        sa.Column('clarity_score', sa.Float(), nullable=False),
        sa.Column('pronunciation_score', sa.Float(), nullable=False),
        sa.Column('confidence_estimate', sa.Float(), nullable=False),
        sa.Column('filler_word_count', sa.Integer(), nullable=False),
        sa.Column('pause_count', sa.Integer(), nullable=False),
        sa.Column('speaking_rate', sa.Float(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('strengths', sa.JSON(), nullable=False),
        sa.Column('weaknesses', sa.JSON(), nullable=False),
        sa.Column('missing_concepts', sa.JSON(), nullable=False),
        sa.Column('feedback', sa.JSON(), nullable=False),
        sa.Column('evaluator_version', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['answer_id'], ['answers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('answer_id')
    )
    op.create_index(op.f('ix_evaluations_answer_id'), 'evaluations', ['answer_id'], unique=True)

    # 9. documents
    op.create_table(
        'documents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_status'), 'documents', ['status'], unique=False)
    op.create_index(op.f('ix_documents_user_id'), 'documents', ['user_id'], unique=False)

    # 10. document_chunks
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('embedding', Vector(1536) if conn.dialect.name == "postgresql" else sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_chunks_document_id'), 'document_chunks', ['document_id'], unique=False)

    # 11. feedback
    op.create_table(
        'feedback',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('interview_id', sa.String(length=36), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=False),
        sa.Column('evidence', sa.Text(), nullable=True),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedback_interview_id'), 'feedback', ['interview_id'], unique=False)

    # 12. learning_recommendations
    op.create_table(
        'learning_recommendations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('interview_id', sa.String(length=36), nullable=True),
        sa.Column('topic', sa.String(length=100), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('recommended_action', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_learning_recommendations_interview_id'), 'learning_recommendations', ['interview_id'], unique=False)
    op.create_index(op.f('ix_learning_recommendations_topic'), 'learning_recommendations', ['topic'], unique=False)
    op.create_index(op.f('ix_learning_recommendations_user_id'), 'learning_recommendations', ['user_id'], unique=False)

    # 13. interview_sessions
    op.create_table(
        'interview_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('interview_id', sa.String(length=36), nullable=False),
        sa.Column('current_state', sa.String(length=50), nullable=False),
        sa.Column('state_metadata', sa.JSON(), nullable=False),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('interview_id')
    )
    op.create_index(op.f('ix_interview_sessions_interview_id'), 'interview_sessions', ['interview_id'], unique=True)


def downgrade() -> None:
    op.drop_table('interview_sessions')
    op.drop_table('learning_recommendations')
    op.drop_table('feedback')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('evaluations')
    op.drop_table('answers')
    op.drop_table('interview_questions')
    op.drop_table('interviews')
    op.drop_table('user_skills')
    op.drop_table('skills')
    op.drop_table('refresh_tokens')
    op.drop_table('users')
