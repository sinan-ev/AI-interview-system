import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
} from 'recharts';
import {
  TrendingUp,
  Target,
  Award,
  Zap,
  BarChart2,
  Calendar,
  Layers,
  ArrowRight,
  AlertTriangle,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { CircularScore } from '../../components/common/CircularScore';
import { ProgressBar } from '../../components/common/ProgressBar';
import { EmptyState } from '../../components/common/EmptyState';
import { PageLoading } from '../../components/common/Spinner';
import { feedbackApi } from '../../api/feedback.api';
import { useAuthStore } from '../../store/authStore';

export const AnalyticsPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const { data: profile, isLoading } = useQuery({
    queryKey: ['performance-profile', user?.id],
    queryFn: () => (user?.id ? feedbackApi.getUserPerformanceProfile(user.id) : Promise.resolve(null)),
    enabled: !!user?.id,
  });

  if (isLoading) {
    return <PageLoading label="Calculating aggregate analytics..." />;
  }

  const summary = profile?.summary;
  const scoreTrend = profile?.score_trend ?? [];
  const topicBreakdown = profile?.topic_breakdown ?? [];
  const weakTopics = profile?.weak_topics ?? [];

  if (!summary || summary.total_interviews === 0) {
    return (
      <div className="max-w-4xl mx-auto py-12">
        <EmptyState
          icon={BarChart2}
          title="No interview analytics yet"
          description="Complete your first interview session to generate comprehensive performance analytics, topic breakdowns, and historical score trajectories."
          action={
            <Button onClick={() => navigate('/interviews/new')}>
              Start First Interview
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-16">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Performance Analytics</h1>
        <p className="text-sm text-text-muted mt-0.5">
          Detailed metrics across technical accuracy, communication fluency, and domain mastery.
        </p>
      </div>

      {/* Primary KPI Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Overall Average', value: `${Math.round(summary.avg_overall)}%`, icon: Award },
          { label: 'Technical Depth', value: `${Math.round(summary.avg_technical)}%`, icon: Target },
          { label: 'Communication', value: `${Math.round(summary.avg_communication)}%`, icon: Zap },
          { label: 'Total Evaluated', value: summary.total_evaluations, icon: TrendingUp },
        ].map((item, i) => (
          <motion.div
            key={item.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <Card padding="md" className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-accent/15 flex items-center justify-center shrink-0">
                <item.icon className="w-5 h-5 text-accent" />
              </div>
              <div>
                <p className="text-xl font-bold text-text-primary">{item.value}</p>
                <p className="text-xs text-text-muted">{item.label}</p>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Trend Chart & Competency Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Chart */}
        <Card padding="lg" className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-text-primary">Performance Trajectory</h2>
            <span className="text-xs text-text-muted">Over Time</span>
          </div>

          <div className="h-64 w-full pt-2">
            {scoreTrend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={scoreTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis
                    dataKey="date"
                    stroke="#64748B"
                    tick={{ fontSize: 11 }}
                    tickFormatter={(val) => new Date(val).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  />
                  <YAxis stroke="#64748B" domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#111827',
                      borderColor: '#1F2937',
                      borderRadius: '0.75rem',
                      color: '#F9FAFB',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="average_score"
                    stroke="#6366F1"
                    strokeWidth={3}
                    dot={{ r: 4, fill: '#6366F1' }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-text-muted">
                Insufficient history to map trend trajectory.
              </div>
            )}
          </div>
        </Card>

        {/* Competencies */}
        <Card padding="lg" className="space-y-4">
          <h2 className="text-base font-semibold text-text-primary">Core Dimensions</h2>
          <div className="space-y-3">
            {[
              { label: 'Technical Accuracy', val: summary.avg_technical },
              { label: 'Communication Clarity', val: summary.avg_communication },
              { label: 'Grammar & Tone', val: summary.avg_grammar },
              { label: 'Fluency & Pacing', val: summary.avg_fluency },
              { label: 'Estimated Confidence', val: summary.avg_confidence },
            ].map(({ label, val }) => (
              <div key={label} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-text-muted">{label}</span>
                  <span className="font-semibold text-text-primary">{Math.round(val)}%</span>
                </div>
                <ProgressBar value={Math.round(val)} max={100} size="sm" variant="accent" />
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Topic Mastery Grid */}
      <Card padding="lg" className="space-y-4">
        <h2 className="text-base font-semibold text-text-primary">Topic Mastery & Coverage</h2>
        {topicBreakdown.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {topicBreakdown.map((t) => (
              <div
                key={t.topic}
                className="p-3.5 rounded-xl bg-background border border-border space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-text-primary truncate">{t.topic}</span>
                  <span
                    className={`text-xs font-bold ${
                      t.average_score >= 80
                        ? 'text-emerald-400'
                        : t.average_score >= 60
                        ? 'text-accent'
                        : 'text-amber-400'
                    }`}
                  >
                    {Math.round(t.average_score)}%
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs text-text-muted">
                  <span>{t.question_count} questions</span>
                  <div className="w-20">
                    <ProgressBar
                      value={Math.round(t.average_score)}
                      max={100}
                      size="sm"
                      variant={t.average_score >= 70 ? 'accent' : 'warning'}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-text-muted">No topic coverage data available.</p>
        )}
      </Card>

      {/* Weak Topics Warning Callout */}
      {weakTopics.length > 0 && (
        <Card padding="lg" className="border-amber-500/20 bg-amber-500/5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              <h2 className="text-base font-semibold text-amber-300">Target Weak Areas</h2>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={() => navigate('/learn')}
              rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
            >
              View Learning Recommendations
            </Button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {weakTopics.map((w) => (
              <div
                key={w.topic}
                className="p-3 rounded-xl bg-card border border-amber-500/20 space-y-1"
              >
                <p className="text-sm font-semibold text-text-primary">{w.topic}</p>
                <p className="text-xs text-amber-400 font-medium">Average: {Math.round(w.average_score)}%</p>
                <p className="text-xs text-text-muted">{w.question_count} answered questions</p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};
