import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Mic,
  Plus,
  Filter,
  Search,
  ArrowRight,
  Calendar,
  CheckCircle2,
  Clock,
  Layers,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { EmptyState } from '../../components/common/EmptyState';
import { PageLoading } from '../../components/common/Spinner';
import { interviewsApi } from '../../api/interviews.api';
import type { InterviewStatus } from '../../types';

export const InterviewListPage: React.FC = () => {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [page, setPage] = useState<number>(1);

  const { data, isLoading } = useQuery({
    queryKey: ['interviews', page, statusFilter],
    queryFn: () =>
      interviewsApi.listInterviews({
        page,
        page_size: 15,
        status: statusFilter || undefined,
      }),
  });

  if (isLoading) {
    return <PageLoading label="Loading interview history..." />;
  }

  const interviews = data?.items ?? [];
  const filteredInterviews = interviews.filter((item) =>
    item.role.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const statusVariant = (status: string) => {
    if (status === 'completed') return 'success';
    if (status === 'in_progress') return 'warning';
    if (status === 'abandoned') return 'error';
    return 'default';
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Interview History</h1>
          <p className="text-sm text-text-muted mt-0.5">
            Review past interview sessions, feedback, and performance progress.
          </p>
        </div>

        <Button
          id="list-new-interview-btn"
          onClick={() => navigate('/interviews/new')}
          leftIcon={<Plus className="w-4 h-4" />}
        >
          New Interview
        </Button>
      </div>

      {/* Filter Bar */}
      <Card padding="sm" className="flex flex-col sm:flex-row items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by role..."
            className="w-full bg-background border border-border text-text-primary placeholder:text-text-muted rounded-xl pl-9 pr-4 py-2 text-sm outline-none focus:border-accent"
          />
        </div>

        {/* Status Filters */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto">
          {[
            { label: 'All', value: '' },
            { label: 'In Progress', value: 'in_progress' },
            { label: 'Completed', value: 'completed' },
            { label: 'Created', value: 'created' },
          ].map((tab) => (
            <button
              key={tab.value}
              onClick={() => {
                setStatusFilter(tab.value);
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                statusFilter === tab.value
                  ? 'bg-accent text-white shadow-sm'
                  : 'bg-background border border-border text-text-muted hover:text-text-primary'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </Card>

      {/* Interview List */}
      {filteredInterviews.length > 0 ? (
        <div className="space-y-3">
          {filteredInterviews.map((interview, idx) => (
            <motion.div
              key={interview.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.04 }}
            >
              <Card
                padding="md"
                className="hover:border-slate-700 transition-all cursor-pointer group"
                onClick={() => navigate(`/interviews/${interview.id}`)}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-start sm:items-center gap-3.5">
                    <div className="w-10 h-10 rounded-xl bg-accent/15 flex items-center justify-center shrink-0 mt-0.5 sm:mt-0">
                      <Mic className="w-5 h-5 text-accent" />
                    </div>
                    <div>
                      <h2 className="text-base font-semibold text-text-primary group-hover:text-accent transition-colors">
                        {interview.role}
                      </h2>
                      <div className="flex items-center gap-2 mt-1 text-xs text-text-muted flex-wrap">
                        <span className="capitalize">{interview.interview_type.replace('_', ' ')}</span>
                        <span>•</span>
                        <span className="capitalize">{interview.difficulty}</span>
                        <span>•</span>
                        <span>{interview.total_questions} Questions</span>
                        <span>•</span>
                        <span>{new Date(interview.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 self-end sm:self-center">
                    {interview.overall_score != null && (
                      <span className="text-base font-bold text-accent">
                        {Math.round(interview.overall_score)}%
                      </span>
                    )}
                    <Badge variant={statusVariant(interview.status)} size="sm">
                      {interview.status.replace('_', ' ')}
                    </Badge>
                    <ArrowRight className="w-4 h-4 text-text-muted group-hover:text-text-primary group-hover:translate-x-0.5 transition-all" />
                  </div>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={Mic}
          title="No interviews found"
          description={
            searchTerm || statusFilter
              ? 'No interviews match your filter criteria.'
              : 'You have not created any interviews yet.'
          }
          action={
            <Button onClick={() => navigate('/interviews/new')} leftIcon={<Plus className="w-4 h-4" />}>
              Create New Interview
            </Button>
          }
        />
      )}
    </div>
  );
};
