import React from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Mic,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  Award,
  ArrowRight,
  RotateCcw,
  BookOpen,
  FileText,
  Clock,
  Sparkles,
  BarChart2,
  ChevronDown,
  Layers,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { CircularScore } from '../../components/common/CircularScore';
import { ProgressBar } from '../../components/common/ProgressBar';
import { PageLoading } from '../../components/common/Spinner';
import { interviewsApi } from '../../api/interviews.api';
import { feedbackApi } from '../../api/feedback.api';
import type { InterviewDetailResponse, InterviewFeedbackResponse } from '../../types';

export const InterviewDetailPage: React.FC = () => {
  const { id: interviewId } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: interview, isLoading: isInterviewLoading } = useQuery({
    queryKey: ['interview-detail', interviewId],
    queryFn: () => (interviewId ? interviewsApi.getInterviewDetail(interviewId) : Promise.reject('No ID')),
    enabled: !!interviewId,
  });

  const { data: feedback, isLoading: isFeedbackLoading } = useQuery({
    queryKey: ['interview-feedback', interviewId],
    queryFn: () => (interviewId ? feedbackApi.getInterviewFeedback(interviewId) : Promise.reject('No ID')),
    enabled: !!interviewId && interview?.status === 'completed',
    retry: 2,
  });

  if (isInterviewLoading || !interview) {
    return <PageLoading label="Loading interview details..." />;
  }

  const isCompleted = interview.status === 'completed';

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <Badge
              variant={isCompleted ? 'success' : interview.status === 'in_progress' ? 'warning' : 'default'}
              size="sm"
            >
              {interview.status.replace('_', ' ')}
            </Badge>
            <span className="text-xs text-text-muted capitalize">
              {interview.interview_type.replace('_', ' ')} · {interview.difficulty}
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-text-primary tracking-tight">
            {interview.role}
          </h1>
          <p className="text-xs text-text-muted mt-1">
            Created on {new Date(interview.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {!isCompleted ? (
            <Button
              id="resume-interview-btn"
              onClick={() => navigate(`/interviews/${interview.id}/room`)}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Resume Interview
            </Button>
          ) : (
            <Button
              variant="secondary"
              id="re-practice-btn"
              onClick={() => navigate('/interviews/new')}
              leftIcon={<RotateCcw className="w-4 h-4" />}
            >
              Practice Again
            </Button>
          )}
        </div>
      </div>

      {/* If Completed: Performance Overview Cards */}
      {isCompleted && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Overall Score Card */}
            <Card padding="lg" className="flex flex-col items-center justify-center text-center">
              <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">
                Overall Performance
              </p>
              <CircularScore
                score={Math.round(feedback?.overall_score ?? interview.overall_score ?? 0)}
                size={110}
                strokeWidth={8}
              />
              <p className="text-xs text-text-muted mt-4">
                Based on {feedback?.total_questions_evaluated ?? interview.questions.length} evaluated questions
              </p>
            </Card>

            {/* Score Breakdown Bars */}
            <Card padding="lg" className="md:col-span-2 space-y-3">
              <h2 className="text-sm font-semibold text-text-primary mb-3">Competency Breakdown</h2>
              {[
                { label: 'Technical Depth', value: feedback?.average_technical_score ?? 0 },
                { label: 'Communication Clarity', value: feedback?.average_communication_score ?? 0 },
                { label: 'Grammar & Accuracy', value: feedback?.average_grammar_score ?? 0 },
                { label: 'Fluency & Pacing', value: feedback?.average_fluency_score ?? 0 },
                { label: 'Confidence Estimate', value: feedback?.average_confidence_score ?? 0 },
              ].map(({ label, value }) => (
                <div key={label} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-text-secondary">{label}</span>
                    <span className="font-semibold text-text-primary">{Math.round(value)}%</span>
                  </div>
                  <ProgressBar value={Math.round(value)} max={100} size="sm" variant="accent" />
                </div>
              ))}
            </Card>
          </div>

          {/* Qualitative Insights */}
          {feedback && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Strengths */}
              <Card padding="md" className="border-emerald-500/20 bg-emerald-500/5">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <h2 className="text-sm font-semibold text-emerald-300">Key Strengths</h2>
                </div>
                {feedback.strengths_summary && feedback.strengths_summary.length > 0 ? (
                  <ul className="space-y-2 text-xs text-text-secondary">
                    {feedback.strengths_summary.map((str, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-emerald-400">•</span>
                        <span>{str}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-text-muted">Consistent foundational answers demonstrated.</p>
                )}
              </Card>

              {/* Weaknesses */}
              <Card padding="md" className="border-amber-500/20 bg-amber-500/5">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  <h2 className="text-sm font-semibold text-amber-300">Areas for Improvement</h2>
                </div>
                {feedback.weaknesses_summary && feedback.weaknesses_summary.length > 0 ? (
                  <ul className="space-y-2 text-xs text-text-secondary">
                    {feedback.weaknesses_summary.map((weak, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-amber-400">•</span>
                        <span>{weak}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-text-muted">No critical weaknesses identified.</p>
                )}
              </Card>
            </div>
          )}

          {/* Missing Concepts Banner */}
          {feedback?.missing_concepts_summary && feedback.missing_concepts_summary.length > 0 && (
            <Card padding="md" className="border-purple-500/20 bg-purple-500/5">
              <h2 className="text-sm font-semibold text-purple-300 mb-2 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" /> Missing Concepts to Review
              </h2>
              <div className="flex flex-wrap gap-2">
                {feedback.missing_concepts_summary.map((concept, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-lg bg-purple-500/15 border border-purple-500/30 text-xs text-purple-200"
                  >
                    {concept}
                  </span>
                ))}
              </div>
            </Card>
          )}
        </>
      )}

      {/* Questions Breakdown */}
      <Card padding="lg" className="space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <h2 className="text-base font-semibold text-text-primary">
            Questions ({interview.questions.length})
          </h2>
          <span className="text-xs text-text-muted">Session Log</span>
        </div>

        {interview.questions.length > 0 ? (
          <div className="space-y-3">
            {interview.questions.map((q) => (
              <div
                key={q.id}
                className="p-4 rounded-xl bg-background border border-border space-y-2"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-md bg-accent/15 text-accent text-xs font-bold flex items-center justify-center">
                      {q.question_number}
                    </span>
                    <Badge variant="accent" size="sm">
                      {q.topic}
                    </Badge>
                    {q.is_follow_up && (
                      <Badge variant="warning" size="sm">
                        Follow-up
                      </Badge>
                    )}
                  </div>
                  <span className="text-xs text-text-muted capitalize">{q.difficulty}</span>
                </div>

                <p className="text-sm font-medium text-text-primary leading-relaxed">
                  {q.question_text}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-text-muted py-4 text-center">
            No questions generated yet for this session.
          </p>
        )}
      </Card>
    </div>
  );
};
