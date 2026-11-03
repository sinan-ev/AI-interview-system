import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Sparkles,
  Layers,
  Sliders,
  Tag,
  Mic,
  FileText,
  Building2,
  ChevronRight,
  Check,
  Plus,
  X,
  HelpCircle,
  FileCode,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { useToast } from '../../components/common/Toast';
import { interviewsApi } from '../../api/interviews.api';
import { documentsApi } from '../../api/documents.api';
import type {
  InterviewCreateRequest,
  InterviewDifficulty,
  InterviewMode,
  InterviewType,
} from '../../types';

const POPULAR_ROLES = [
  'Senior Backend Engineer',
  'Full Stack Developer',
  'Frontend Engineer',
  'Distributed Systems Architect',
  'DevOps / SRE Engineer',
  'Machine Learning Engineer',
  'Data Engineer',
  'Engineering Manager',
  'Product Manager',
  'HR / Behavioral Candidate',
];

const INTERVIEW_TYPES: { type: InterviewType; label: string; desc: string; icon: string }[] = [
  {
    type: 'technical',
    label: 'Technical Deep-Dive',
    desc: 'Core computer science, architecture, concurrency, and algorithms.',
    icon: '⚡',
  },
  {
    type: 'company_style',
    label: 'Company Specific',
    desc: 'Simulate high-bar interview loops like Google, Meta, Amazon, or Netflix.',
    icon: '🏢',
  },
  {
    type: 'topic_specific',
    label: 'Targeted Topics',
    desc: 'Laser-focus on specific domains such as PostgreSQL, Redis, or Microservices.',
    icon: '🎯',
  },
  {
    type: 'document_based',
    label: 'Document / RAG',
    desc: 'Interview based entirely on uploaded technical documents, specs, or designs.',
    icon: '📄',
  },
  {
    type: 'resume_based',
    label: 'Resume Based',
    desc: 'Deep questions tailored to past career experience from your uploaded resume.',
    icon: '📑',
  },
  {
    type: 'hr',
    label: 'Behavioral & Leadership',
    desc: 'Conflict resolution, leadership principles, STAR method evaluation.',
    icon: '🤝',
  },
  {
    type: 'mixed',
    label: 'Comprehensive Mixed',
    desc: 'Balanced combination of technical depth, system design, and soft skills.',
    icon: '🌟',
  },
  {
    type: 'general',
    label: 'Standard Practice',
    desc: 'Broad general questions suited for quick warm-ups and baseline checks.',
    icon: '💡',
  },
];

const DIFFICULTY_LEVELS: { level: InterviewDifficulty; label: string; desc: string; badge: string }[] = [
  { level: 'beginner', label: 'Junior / Beginner', desc: 'Foundational concepts and principles', badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
  { level: 'intermediate', label: 'Mid-Level', desc: 'Practical tradeoffs, debugging, and patterns', badge: 'bg-accent/10 text-accent border-accent/20' },
  { level: 'advanced', label: 'Senior / Staff', desc: 'High-scale architecture, edge cases, deep internals', badge: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
];

const POPULAR_COMPANIES = [
  'Google',
  'Amazon',
  'Meta',
  'Microsoft',
  'Apple',
  'Netflix',
  'Uber',
  'Stripe',
];

const SUGGESTED_TOPICS = [
  'System Design',
  'Algorithms & Data Structures',
  'Concurrency & Multithreading',
  'PostgreSQL & Database Internals',
  'Distributed Caching & Redis',
  'REST API & gRPC',
  'Microservices Architecture',
  'Security & Authentication',
  'Python Fast-Paths',
  'React Performance & State',
  'Containerization & Kubernetes',
  'Behavioral & STAR Method',
];

export const NewInterviewPage: React.FC = () => {
  const navigate = useNavigate();
  const { error, success } = useToast();

  const [role, setRole] = useState('Senior Backend Engineer');
  const [customRole, setCustomRole] = useState('');
  const [interviewType, setInterviewType] = useState<InterviewType>('technical');
  const [difficulty, setDifficulty] = useState<InterviewDifficulty>('intermediate');
  const [mode, setMode] = useState<InterviewMode>('text');
  const [questionCount, setQuestionCount] = useState(5);
  const [selectedTopics, setSelectedTopics] = useState<string[]>(['System Design', 'PostgreSQL & Database Internals']);
  const [customTopicInput, setCustomTopicInput] = useState('');
  const [companyStyle, setCompanyStyle] = useState<string>('');
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch uploaded documents if document or resume type selected
  const { data: documentsData } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentsApi.listDocuments(),
    enabled: interviewType === 'document_based' || interviewType === 'resume_based',
  });

  const activeRole = customRole.trim() ? customRole.trim() : role;

  const toggleTopic = (topic: string) => {
    setSelectedTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]
    );
  };

  const addCustomTopic = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customTopicInput.trim()) return;
    const clean = customTopicInput.trim();
    if (!selectedTopics.includes(clean)) {
      setSelectedTopics((prev) => [...prev, clean]);
    }
    setCustomTopicInput('');
  };

  const removeTopic = (topic: string) => {
    setSelectedTopics((prev) => prev.filter((t) => t !== topic));
  };

  const toggleDocument = (docId: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  const handleSubmit = async () => {
    if (!activeRole) {
      error('Please select or enter an interview target role.');
      return;
    }
    if (selectedTopics.length === 0) {
      error('Please select at least one topic for your interview.');
      return;
    }
    if ((interviewType === 'document_based' || interviewType === 'resume_based') && selectedDocIds.length === 0) {
      error('Please select at least one uploaded document for document-based interviews.');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload: InterviewCreateRequest = {
        role: activeRole,
        interview_type: interviewType,
        difficulty,
        topics: selectedTopics,
        question_count: questionCount,
        mode,
        company_style: companyStyle || undefined,
        document_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
      };

      const interview = await interviewsApi.createInterview(payload);
      success('Interview configured successfully! Starting session...');
      // Start the interview to initialize session
      await interviewsApi.startInterview(interview.id);
      navigate(`/interviews/${interview.id}/room`);
    } catch (err: any) {
      const msg = err?.response?.data?.error?.message || err?.message || 'Failed to initialize interview.';
      error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Badge variant="accent" size="sm">Session Setup</Badge>
          <span className="text-xs text-text-muted">Dynamic AI Generator</span>
        </div>
        <h1 className="text-3xl font-bold text-text-primary tracking-tight">Configure Interview</h1>
        <p className="text-text-muted mt-1 text-sm">
          Customize your role, difficulty, topics, and interview style. Questions adapt dynamically based on your answers.
        </p>
      </div>

      {/* Step 1: Target Role */}
      <Card padding="lg" className="space-y-4">
        <div className="flex items-center gap-2 border-b border-border pb-3">
          <div className="w-7 h-7 rounded-lg bg-accent/10 flex items-center justify-center">
            <span className="text-xs font-bold text-accent">1</span>
          </div>
          <h2 className="text-lg font-semibold text-text-primary">Target Role</h2>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {POPULAR_ROLES.map((r) => {
            const isSelected = role === r && !customRole;
            return (
              <button
                key={r}
                type="button"
                onClick={() => {
                  setRole(r);
                  setCustomRole('');
                }}
                className={`p-3 rounded-xl border text-left text-sm font-medium transition-all ${
                  isSelected
                    ? 'border-accent bg-accent/10 text-accent font-semibold shadow-sm'
                    : 'border-border bg-slate-900/40 text-text-secondary hover:border-slate-600 hover:text-text-primary'
                }`}
              >
                {r}
              </button>
            );
          })}
        </div>

        <div className="pt-2">
          <label className="block text-xs font-medium text-text-muted mb-1.5">
            Or type a custom role title:
          </label>
          <input
            type="text"
            value={customRole}
            onChange={(e) => setCustomRole(e.target.value)}
            placeholder="e.g. Lead Blockchain Protocol Architect"
            className="w-full bg-background border border-border text-text-primary placeholder:text-text-muted rounded-xl px-4 py-2.5 text-sm outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 transition-all"
          />
        </div>
      </Card>

      {/* Step 2: Interview Style & Format */}
      <Card padding="lg" className="space-y-4">
        <div className="flex items-center gap-2 border-b border-border pb-3">
          <div className="w-7 h-7 rounded-lg bg-accent/10 flex items-center justify-center">
            <span className="text-xs font-bold text-accent">2</span>
          </div>
          <h2 className="text-lg font-semibold text-text-primary">Interview Style</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {INTERVIEW_TYPES.map((t) => {
            const isSelected = interviewType === t.type;
            return (
              <button
                key={t.type}
                type="button"
                onClick={() => setInterviewType(t.type)}
                className={`flex items-start gap-3 p-3.5 rounded-xl border text-left transition-all ${
                  isSelected
                    ? 'border-accent bg-accent/10 text-text-primary shadow-sm'
                    : 'border-border bg-slate-900/40 text-text-muted hover:border-slate-600 hover:text-text-secondary'
                }`}
              >
                <span className="text-2xl">{t.icon}</span>
                <div>
                  <p className={`text-sm font-semibold ${isSelected ? 'text-accent' : 'text-text-primary'}`}>
                    {t.label}
                  </p>
                  <p className="text-xs text-text-muted mt-0.5 leading-relaxed">{t.desc}</p>
                </div>
              </button>
            );
          })}
        </div>

        {/* Company Style if selected */}
        {(interviewType === 'company_style' || companyStyle) && (
          <div className="pt-3 border-t border-border/60">
            <label className="block text-xs font-medium text-text-secondary mb-2">
              Select Company Evaluation Style:
            </label>
            <div className="flex flex-wrap gap-2">
              {POPULAR_COMPANIES.map((comp) => {
                const isSelected = companyStyle.toLowerCase() === comp.toLowerCase();
                return (
                  <button
                    key={comp}
                    type="button"
                    onClick={() => setCompanyStyle(isSelected ? '' : comp)}
                    className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
                      isSelected
                        ? 'border-accent bg-accent/20 text-accent font-semibold'
                        : 'border-border bg-background text-text-muted hover:border-slate-600'
                    }`}
                  >
                    {comp}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Document Selector if document or resume based */}
        {(interviewType === 'document_based' || interviewType === 'resume_based') && (
          <div className="pt-3 border-t border-border/60">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-medium text-text-secondary">
                Select Source Documents (RAG Knowledge Base):
              </label>
              <button
                type="button"
                onClick={() => navigate('/documents')}
                className="text-xs text-accent hover:underline flex items-center gap-1"
              >
                Manage Documents <ChevronRight className="w-3 h-3" />
              </button>
            </div>
            {documentsData && documentsData.documents.length > 0 ? (
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {documentsData.documents.map((doc) => {
                  const isChecked = selectedDocIds.includes(doc.document_id);
                  return (
                    <div
                      key={doc.document_id}
                      onClick={() => toggleDocument(doc.document_id)}
                      className={`flex items-center justify-between p-2.5 rounded-xl border cursor-pointer transition-all ${
                        isChecked
                          ? 'border-accent bg-accent/10 text-text-primary'
                          : 'border-border bg-slate-900/30 text-text-muted hover:border-slate-600'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <FileCode className="w-4 h-4 text-accent" />
                        <div>
                          <p className="text-sm font-medium text-text-primary">{doc.title}</p>
                          <p className="text-xs text-text-muted">{doc.file_type.toUpperCase()} · {doc.chunk_count} chunks</p>
                        </div>
                      </div>
                      <div className={`w-5 h-5 rounded-md border flex items-center justify-center ${isChecked ? 'bg-accent border-accent text-white' : 'border-slate-700'}`}>
                        {isChecked && <Check className="w-3 h-3" />}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-slate-900/60 border border-border text-center">
                <p className="text-xs text-text-muted mb-2">No uploaded documents found.</p>
                <Button size="sm" variant="secondary" onClick={() => navigate('/documents')}>
                  Upload Document Now
                </Button>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Step 3: Difficulty & Parameters */}
      <Card padding="lg" className="space-y-6">
        <div className="flex items-center gap-2 border-b border-border pb-3">
          <div className="w-7 h-7 rounded-lg bg-accent/10 flex items-center justify-center">
            <span className="text-xs font-bold text-accent">3</span>
          </div>
          <h2 className="text-lg font-semibold text-text-primary">Difficulty & Parameters</h2>
        </div>

        {/* Difficulty */}
        <div>
          <label className="block text-xs font-medium text-text-muted mb-2.5">Target Difficulty:</label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {DIFFICULTY_LEVELS.map((d) => {
              const isSelected = difficulty === d.level;
              return (
                <button
                  key={d.level}
                  type="button"
                  onClick={() => setDifficulty(d.level)}
                  className={`p-3.5 rounded-xl border text-left transition-all ${
                    isSelected
                      ? `${d.badge} font-semibold ring-1 ring-accent/30`
                      : 'border-border bg-slate-900/40 text-text-muted hover:border-slate-600'
                  }`}
                >
                  <p className="text-sm font-semibold text-text-primary">{d.label}</p>
                  <p className="text-xs text-text-muted mt-1">{d.desc}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Mode & Question Count */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
          {/* Mode */}
          <div>
            <label className="block text-xs font-medium text-text-muted mb-2">Interview Response Mode:</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setMode('text')}
                className={`p-3 rounded-xl border flex items-center gap-2.5 transition-all ${
                  mode === 'text'
                    ? 'border-accent bg-accent/10 text-accent font-semibold'
                    : 'border-border bg-slate-900/40 text-text-muted hover:border-slate-600'
                }`}
              >
                <FileText className="w-4 h-4" />
                <span className="text-sm">Text Written</span>
              </button>

              <button
                type="button"
                onClick={() => setMode('voice')}
                className={`p-3 rounded-xl border flex items-center gap-2.5 transition-all ${
                  mode === 'voice'
                    ? 'border-accent bg-accent/10 text-accent font-semibold'
                    : 'border-border bg-slate-900/40 text-text-muted hover:border-slate-600'
                }`}
              >
                <Mic className="w-4 h-4" />
                <span className="text-sm">Voice Spoken</span>
              </button>
            </div>
          </div>

          {/* Question Count */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-medium text-text-muted">Questions to Ask:</label>
              <span className="text-sm font-bold text-accent">{questionCount} Questions</span>
            </div>
            <input
              type="range"
              min={3}
              max={12}
              step={1}
              value={questionCount}
              onChange={(e) => setQuestionCount(Number(e.target.value))}
              className="w-full accent-accent cursor-pointer"
            />
            <div className="flex justify-between text-[11px] text-text-muted mt-1">
              <span>3 (Quick)</span>
              <span>5 (Standard)</span>
              <span>8 (Full Loop)</span>
              <span>12 (Comprehensive)</span>
            </div>
          </div>
        </div>
      </Card>

      {/* Step 4: Focus Topics */}
      <Card padding="lg" className="space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-accent/10 flex items-center justify-center">
              <span className="text-xs font-bold text-accent">4</span>
            </div>
            <h2 className="text-lg font-semibold text-text-primary">Focus Topics</h2>
          </div>
          <span className="text-xs text-text-muted">{selectedTopics.length} selected</span>
        </div>

        {/* Selected topic chips */}
        <div className="flex flex-wrap gap-2 min-h-10 p-2.5 rounded-xl bg-background border border-border">
          {selectedTopics.length === 0 ? (
            <p className="text-xs text-text-muted italic py-1">No topics selected. Pick from suggestions below.</p>
          ) : (
            selectedTopics.map((topic) => (
              <span
                key={topic}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-accent/15 border border-accent/30 text-xs font-medium text-accent"
              >
                {topic}
                <button
                  type="button"
                  onClick={() => removeTopic(topic)}
                  className="hover:text-white transition-colors"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))
          )}
        </div>

        {/* Add custom topic form */}
        <form onSubmit={addCustomTopic} className="flex gap-2">
          <input
            type="text"
            value={customTopicInput}
            onChange={(e) => setCustomTopicInput(e.target.value)}
            placeholder="Add custom topic (e.g. Raft Consensus, Bloom Filters)..."
            className="flex-1 bg-background border border-border text-text-primary placeholder:text-text-muted rounded-xl px-4 py-2 text-sm outline-none focus:border-accent"
          />
          <Button type="submit" variant="secondary" size="sm" leftIcon={<Plus className="w-3.5 h-3.5" />}>
            Add Topic
          </Button>
        </form>

        {/* Suggested topics list */}
        <div>
          <p className="text-xs font-medium text-text-muted mb-2">Quick Pick Suggestions:</p>
          <div className="flex flex-wrap gap-1.5">
            {SUGGESTED_TOPICS.map((topic) => {
              const isSelected = selectedTopics.includes(topic);
              return (
                <button
                  key={topic}
                  type="button"
                  onClick={() => toggleTopic(topic)}
                  className={`px-2.5 py-1 rounded-lg border text-xs transition-all ${
                    isSelected
                      ? 'border-accent bg-accent/20 text-accent font-medium'
                      : 'border-border bg-slate-900/40 text-text-muted hover:border-slate-700 hover:text-text-secondary'
                  }`}
                >
                  {isSelected && '✓ '}
                  {topic}
                </button>
              );
            })}
          </div>
        </div>
      </Card>

      {/* Action Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-border">
        <Button variant="ghost" onClick={() => navigate('/dashboard')}>
          Cancel
        </Button>

        <Button
          id="start-interview-submit-btn"
          size="lg"
          isLoading={isSubmitting}
          onClick={handleSubmit}
          rightIcon={<ChevronRight className="w-4 h-4" />}
        >
          Launch Interview Session
        </Button>
      </div>
    </div>
  );
};
