import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  BookOpen,
  Sparkles,
  Zap,
  ArrowRight,
  ExternalLink,
  Target,
  AlertCircle,
  CheckCircle2,
  Bookmark,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { EmptyState } from '../../components/common/EmptyState';
import { PageLoading } from '../../components/common/Spinner';
import { feedbackApi } from '../../api/feedback.api';
import { useAuthStore } from '../../store/authStore';

export const LearnPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const { data: profile, isLoading } = useQuery({
    queryKey: ['performance-profile', user?.id],
    queryFn: () => (user?.id ? feedbackApi.getUserPerformanceProfile(user.id) : Promise.resolve(null)),
    enabled: !!user?.id,
  });

  if (isLoading) {
    return <PageLoading label="Curating personalized learning recommendations..." />;
  }

  const recommendations = profile?.learning_recommendations ?? [];

  const priorityBadge = (priority: string) => {
    if (priority === 'high') return <Badge variant="error" size="sm">High Priority</Badge>;
    if (priority === 'medium') return <Badge variant="warning" size="sm">Medium Priority</Badge>;
    return <Badge variant="default" size="sm">Low Priority</Badge>;
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1.5">
          <Badge variant="accent" size="sm">AI Study Plan</Badge>
          <span className="text-xs text-text-muted">Targeted Improvement</span>
        </div>
        <h1 className="text-2xl font-bold text-text-primary">Personalized Learning Recommendations</h1>
        <p className="text-sm text-text-muted mt-0.5">
          Generated automatically from weak concepts, missing fundamentals, and response accuracy in your past interviews.
        </p>
      </div>

      {/* Recommendations List */}
      {recommendations.length > 0 ? (
        <div className="space-y-4">
          {recommendations.map((item, idx) => (
            <motion.div
              key={item.topic + idx}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
            >
              <Card padding="lg" className="space-y-3 border-accent/20">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <h2 className="text-base font-bold text-text-primary">{item.topic}</h2>
                    {priorityBadge(item.priority)}
                  </div>

                  <Button
                    size="sm"
                    onClick={() => navigate('/interviews/new')}
                    rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                  >
                    Practice This Topic
                  </Button>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/40 border border-border">
                  <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-1">
                    Why this was recommended:
                  </p>
                  <p className="text-xs text-text-secondary leading-relaxed">{item.reason}</p>
                </div>

                <div>
                  <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-1">
                    Suggested Action:
                  </p>
                  <p className="text-sm font-medium text-text-primary leading-relaxed">
                    {item.suggested_action}
                  </p>
                </div>

                {item.resources && item.resources.length > 0 && (
                  <div className="pt-2 border-t border-border">
                    <p className="text-xs font-semibold text-text-muted mb-2">Recommended Study Resources:</p>
                    <div className="flex flex-wrap gap-2">
                      {item.resources.map((res, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-background border border-border text-xs text-text-secondary"
                        >
                          <BookOpen className="w-3 h-3 text-accent" />
                          <span>{res}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            </motion.div>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={BookOpen}
          title="No recommendations generated yet"
          description="Take an interview to discover targeted weak topics and receive tailored learning action plans."
          action={
            <Button onClick={() => navigate('/interviews/new')}>
              Start First Interview
            </Button>
          }
        />
      )}
    </div>
  );
};
