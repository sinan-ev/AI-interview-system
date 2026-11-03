import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import {
  Mic,
  TrendingUp,
  CheckCircle2,
  Clock,
  ArrowRight,
  Plus,
  BarChart2,
  Zap,
  Target,
  BookOpen,
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { interviewsApi } from '../../api/interviews.api';
import { feedbackApi } from '../../api/feedback.api';
import { PageLoading } from '../../components/common/Spinner';
import { Card } from '../../components/common/Card';
import { Badge } from '../../components/common/Badge';
import { Button } from '../../components/common/Button';
import { CircularScore } from '../../components/common/CircularScore';
import { EmptyState } from '../../components/common/EmptyState';
import type { InterviewResponse, UserPerformanceProfile } from '../../types';

// ── helpers ──────────────────────────────────────────────
const statusVariant = (status: string) => {
  if (status === 'completed') return 'success';
  if (status === 'in_progress') return 'warning';
  if (status === 'abandoned') return 'error';
  return 'default';
};

const formatDate = (iso: string | null) => {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

// ── sub-components ────────────────────────────────────────
const StatCard: React.FC<{
  label: string;
  value: string | number;
  icon: React.ElementType;
  sub?: string;
  delay?: number;
}> = ({ label, value, icon: Icon, sub, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 12 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay, duration: 0.3 }}
  >
    <Card className="flex items-start gap-4">
      <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center shrink-0">
        <Icon className="w-5 h-5 text-accent" />
      </div>
      <div>
        <p className="text-2xl font-bold text-text-primary">{value}</p>
        <p className="text-sm font-medium text-text-secondary">{label}</p>
        {sub && <p className="text-xs text-text-muted mt-0.5">{sub}</p>}
      </div>
    </Card>
  </motion.div>
);

const InterviewRow: React.FC<{ interview: InterviewResponse; index: number }> = ({
  interview,
  index,
}) => {
  const navigate = useNavigate();

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05, duration: 0.25 }}
      className="flex items-center justify-between py-3 border-b border-border last:border-0 hover:bg-slate-800/30 -mx-4 px-4 rounded-lg cursor-pointer transition-colors"
      onClick={() => navigate(`/interviews/${interview.id}`)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && navigate(`/interviews/${interview.id}`)}
    >
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center shrink-0">
          <Mic className="w-3.5 h-3.5 text-text-muted" />
        </div>
        <div>
          <p className="text-sm font-medium text-text-primary">{interview.role}</p>
          <p className="text-xs text-text-muted capitalize">
            {interview.interview_type?.replace('_', ' ')} · {formatDate(interview.created_at)}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        {interview.overall_score != null && (
          <span className="text-sm font-semibold text-accent">{Math.round(interview.overall_score)}%</span>
        )}
        <Badge variant={statusVariant(interview.status)} size="sm">
          {interview.status.replace('_', ' ')}
        </Badge>
        <ArrowRight className="w-3.5 h-3.5 text-text-muted" />
      </div>
    </motion.div>
  );
};

// ── page ─────────────────────────────────────────────────
export const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const { data: interviewsData, isLoading: interviewsLoading } = useQuery({
    queryKey: ['interviews', 'recent'],
    queryFn: () => interviewsApi.listInterviews({ page: 1, page_size: 5 }),
  });

  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ['performance-profile', user?.id],
    queryFn: () => (user?.id ? feedbackApi.getUserPerformanceProfile(user.id) : Promise.resolve(null)),
    enabled: !!user?.id,
  });

  const isLoading = interviewsLoading && profileLoading;
  if (isLoading) return <PageLoading label="Loading your dashboard..." />;

  const stats = profile?.summary;
  const recentInterviews = interviewsData?.items ?? [];

  const greetingHour = new Date().getHours();
  const greeting =
    greetingHour < 12 ? 'Good morning' : greetingHour < 17 ? 'Good afternoon' : 'Good evening';

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <motion.h1
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-2xl font-bold text-text-primary"
          >
            {greeting}, {user?.name?.split(' ')[0]} 👋
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-text-muted mt-1"
          >
            Here's how your practice is going.
          </motion.p>
        </div>
        <Button
          id="dashboard-new-interview-btn"
          onClick={() => navigate('/interviews/new')}
          leftIcon={<Plus className="w-4 h-4" />}
        >
          New Interview
        </Button>
      </div>

      {/* Stat Cards */}
      {stats ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            label="Total Interviews"
            value={stats.total_interviews}
            icon={Mic}
            delay={0.05}
          />
          <StatCard
            label="Avg Overall Score"
            value={`${Math.round(stats.avg_overall)}%`}
            icon={TrendingUp}
            delay={0.1}
          />
          <StatCard
            label="Evaluations"
            value={stats.total_evaluations}
            icon={CheckCircle2}
            delay={0.15}
          />
          <StatCard
            label="Avg Technical"
            value={`${Math.round(stats.avg_technical)}%`}
            icon={Target}
            delay={0.2}
          />
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-2xl bg-card border border-border animate-pulse" />
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Interviews */}
        <Card className="lg:col-span-2" padding="md">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-text-primary">Recent Interviews</h2>
            <Link
              to="/interviews"
              id="dashboard-view-all-interviews"
              className="text-xs text-accent hover:text-accent/80 flex items-center gap-1 transition-colors"
            >
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {recentInterviews.length > 0 ? (
            recentInterviews.map((interview, idx) => (
              <InterviewRow key={interview.id} interview={interview} index={idx} />
            ))
          ) : (
            <EmptyState
              icon={Mic}
              title="No interviews yet"
              description="Start your first interview to see your progress here."
              action={
                <Button
                  size="sm"
                  id="dashboard-empty-start-interview"
                  onClick={() => navigate('/interviews/new')}
                  leftIcon={<Plus className="w-3.5 h-3.5" />}
                >
                  Start Interview
                </Button>
              }
            />
          )}
        </Card>

        {/* Score Summary */}
        <div className="space-y-4">
          {stats ? (
            <>
              <Card padding="md">
                <h2 className="text-base font-semibold text-text-primary mb-4">Score Breakdown</h2>
                <div className="flex justify-center mb-4">
                  <CircularScore score={Math.round(stats.avg_overall)} size={90} strokeWidth={6} />
                </div>
                <div className="space-y-2.5">
                  {[
                    { label: 'Technical', value: stats.avg_technical },
                    { label: 'Communication', value: stats.avg_communication },
                    { label: 'Grammar', value: stats.avg_grammar },
                    { label: 'Fluency', value: stats.avg_fluency },
                    { label: 'Confidence', value: stats.avg_confidence },
                  ].map(({ label, value }) => (
                    <div key={label} className="flex items-center gap-2">
                      <span className="text-xs text-text-muted w-24 shrink-0">{label}</span>
                      <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${value}%` }}
                          transition={{ delay: 0.3, duration: 0.6 }}
                          className="h-full bg-accent rounded-full"
                        />
                      </div>
                      <span className="text-xs font-medium text-text-secondary w-8 text-right">
                        {Math.round(value)}%
                      </span>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Quick actions */}
              <Card padding="md">
                <h2 className="text-base font-semibold text-text-primary mb-3">Quick Actions</h2>
                <div className="space-y-2">
                  {[
                    { label: 'New Interview', icon: Mic, to: '/interviews/new' },
                    { label: 'View Analytics', icon: BarChart2, to: '/analytics' },
                    { label: 'Upload Document', icon: BookOpen, to: '/documents' },
                    { label: 'Learning Plan', icon: Zap, to: '/learn' },
                  ].map(({ label, icon: Icon, to }) => (
                    <Link
                      key={to}
                      to={to}
                      id={`dashboard-quick-${label.toLowerCase().replace(' ', '-')}`}
                      className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-slate-800/60 transition-colors group"
                    >
                      <Icon className="w-4 h-4 text-text-muted group-hover:text-accent transition-colors" />
                      <span className="text-sm text-text-secondary group-hover:text-text-primary transition-colors">
                        {label}
                      </span>
                      <ArrowRight className="w-3.5 h-3.5 text-text-muted ml-auto opacity-0 group-hover:opacity-100 transition-all" />
                    </Link>
                  ))}
                </div>
              </Card>
            </>
          ) : (
            // Getting started card when no profile exists
            <Card padding="md" className="border-accent/20">
              <div className="flex items-center gap-2 mb-3">
                <Zap className="w-4 h-4 text-accent" />
                <h2 className="text-base font-semibold text-text-primary">Get Started</h2>
              </div>
              <p className="text-sm text-text-muted mb-4">
                Complete your first interview to unlock your performance profile, score breakdown, and personalized learning recommendations.
              </p>
              <Button
                size="sm"
                id="dashboard-get-started-btn"
                className="w-full"
                onClick={() => navigate('/interviews/new')}
                leftIcon={<Plus className="w-3.5 h-3.5" />}
              >
                Start First Interview
              </Button>
            </Card>
          )}
        </div>
      </div>

      {/* Weak Topics */}
      {profile?.weak_topics && profile.weak_topics.length > 0 && (
        <Card padding="md">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-text-primary">Topics to Improve</h2>
            <Link
              to="/learn"
              id="dashboard-view-all-topics"
              className="text-xs text-accent hover:text-accent/80 flex items-center gap-1 transition-colors"
            >
              See recommendations <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {profile.weak_topics.slice(0, 6).map((topic, i) => (
              <motion.div
                key={topic.topic}
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-center gap-3 p-3 rounded-xl bg-error/5 border border-error/15"
              >
                <div className="w-8 h-8 rounded-lg bg-error/10 flex items-center justify-center shrink-0">
                  <span className="text-xs font-bold text-error">{Math.round(topic.average_score)}%</span>
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-text-primary truncate">{topic.topic}</p>
                  <p className="text-xs text-text-muted">{topic.question_count} questions</p>
                </div>
              </motion.div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};
