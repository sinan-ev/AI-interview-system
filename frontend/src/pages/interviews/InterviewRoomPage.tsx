import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Mic,
  MicOff,
  Square,
  Play,
  RotateCcw,
  Volume2,
  VolumeX,
  Send,
  Sparkles,
  ChevronRight,
  CheckCircle,
  AlertCircle,
  HelpCircle,
  Clock,
  Award,
  Layers,
  ArrowRight,
  TrendingUp,
  Brain,
  ListOrdered,
  FileCheck,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { ProgressBar } from '../../components/common/ProgressBar';
import { CircularScore } from '../../components/common/CircularScore';
import { Modal } from '../../components/common/Modal';
import { Spinner, PageLoading } from '../../components/common/Spinner';
import { useToast } from '../../components/common/Toast';
import { interviewsApi } from '../../api/interviews.api';
import { answersApi } from '../../api/answers.api';
import { feedbackApi } from '../../api/feedback.api';
import type {
  InterviewDetailResponse,
  QuestionResponse,
  EvaluationResponse,
} from '../../types';

export const InterviewRoomPage: React.FC = () => {
  const { id: interviewId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { error, success, info } = useToast();

  // State
  const [activeQuestion, setActiveQuestion] = useState<QuestionResponse | null>(null);
  const [textAnswer, setTextAnswer] = useState('');
  const [inputMode, setInputMode] = useState<'text' | 'voice'>('text');
  const [isSpeakingQuestion, setIsSpeakingQuestion] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [latestEvaluation, setLatestEvaluation] = useState<EvaluationResponse | null>(null);
  const [showEvaluationModal, setShowEvaluationModal] = useState(false);

  // Audio Recording State
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [liveTranscript, setLiveTranscript] = useState('');

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerIntervalRef = useRef<any>(null);
  const recognitionRef = useRef<any>(null);

  // Fetch Interview Details
  const {
    data: interview,
    isLoading: isInterviewLoading,
    refetch: refetchInterview,
  } = useQuery({
    queryKey: ['interview', interviewId],
    queryFn: () => (interviewId ? interviewsApi.getInterviewDetail(interviewId) : Promise.reject('No ID')),
    enabled: !!interviewId,
  });

  // Fetch or Generate Active Question
  const fetchCurrentQuestion = async () => {
    if (!interviewId) return;
    try {
      const q = await interviewsApi.getCurrentQuestion(interviewId);
      setActiveQuestion(q);
      setTextAnswer('');
      setAudioBlob(null);
      setAudioUrl(null);
      setLiveTranscript('');
      setRecordingSeconds(0);
    } catch (err: any) {
      const msg = err?.response?.data?.error?.message || 'Could not fetch current question.';
      error(msg);
    }
  };

  useEffect(() => {
    if (interview) {
      if (interview.status === 'completed') {
        navigate(`/interviews/${interview.id}`);
        return;
      }
      if (interview.configuration?.mode) {
        setInputMode(interview.configuration.mode);
      }
      fetchCurrentQuestion();
    }
  }, [interview?.id]);

  // Read question text aloud using browser SpeechSynthesis
  const handleSpeakQuestion = () => {
    if (!activeQuestion) return;
    if ('speechSynthesis' in window) {
      if (isSpeakingQuestion) {
        window.speechSynthesis.cancel();
        setIsSpeakingQuestion(false);
        return;
      }
      const utterance = new SpeechSynthesisUtterance(activeQuestion.question_text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.onend = () => setIsSpeakingQuestion(false);
      utterance.onerror = () => setIsSpeakingQuestion(false);
      setIsSpeakingQuestion(true);
      window.speechSynthesis.speak(utterance);
    } else {
      info('Speech synthesis is not supported on this browser.');
    }
  };

  // Web Audio MediaRecorder setup
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const recorder = new MediaRecorder(stream);

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start(250);
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
      setRecordingSeconds(0);

      timerIntervalRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);

      // Web Speech API for live transcription if supported
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        try {
          const rec = new SpeechRecognition();
          rec.continuous = true;
          rec.interimResults = true;
          rec.lang = 'en-US';
          rec.onresult = (event: any) => {
            let transcriptText = '';
            for (let i = 0; i < event.results.length; i++) {
              transcriptText += event.results[i][0].transcript + ' ';
            }
            setLiveTranscript(transcriptText);
          };
          rec.start();
          recognitionRef.current = rec;
        } catch {
          // Ignore recognition failure, fallback to recording
        }
      }
    } catch (err: any) {
      error('Microphone access denied or audio device not found.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {}
    }
    clearInterval(timerIntervalRef.current);
    setIsRecording(false);
  };

  const resetRecording = () => {
    stopRecording();
    setAudioBlob(null);
    setAudioUrl(null);
    setLiveTranscript('');
    setRecordingSeconds(0);
  };

  // Submit Answer (Text or Audio)
  const handleSubmitAnswer = async () => {
    if (!interviewId || !activeQuestion) return;

    if (inputMode === 'text' && !textAnswer.trim()) {
      error('Please write an answer before submitting.');
      return;
    }
    if (inputMode === 'voice' && !audioBlob && !textAnswer.trim()) {
      error('Please record your voice response before submitting.');
      return;
    }

    setIsEvaluating(true);
    try {
      let answerResult;
      if (inputMode === 'voice' && audioBlob) {
        answerResult = await answersApi.submitVoiceAnswer(interviewId, {
          questionId: activeQuestion.id,
          audioBlob: audioBlob,
          durationSeconds: recordingSeconds,
          transcript: liveTranscript.trim() || undefined,
        });
      } else {
        answerResult = await answersApi.submitTextAnswer(interviewId, {
          question_id: activeQuestion.id,
          text_answer: textAnswer.trim(),
        });
      }

      success('Answer received! Analyzing technical depth and communication...');

      // Attempt to retrieve instant answer evaluation
      try {
        const evalData = await feedbackApi.getAnswerEvaluation(answerResult.id);
        setLatestEvaluation(evalData);
        setShowEvaluationModal(true);
      } catch {
        // If background evaluation takes longer, move directly to next question
        handleAdvanceQuestion();
      }
    } catch (err: any) {
      const msg = err?.response?.data?.error?.message || 'Failed to submit answer.';
      error(msg);
    } finally {
      setIsEvaluating(false);
    }
  };

  // Advance to Next Question or Complete Interview
  const handleAdvanceQuestion = async () => {
    setShowEvaluationModal(false);
    setLatestEvaluation(null);
    await refetchInterview();

    const isLastQuestion =
      interview &&
      interview.current_question >= interview.total_questions;

    if (isLastQuestion) {
      handleCompleteInterview();
    } else {
      await fetchCurrentQuestion();
    }
  };

  const handleCompleteInterview = async () => {
    if (!interviewId) return;
    try {
      await interviewsApi.completeInterview(interviewId);
      success('Interview completed! Generating full performance analytics...');
      navigate(`/interviews/${interviewId}`);
    } catch (err: any) {
      const msg = err?.response?.data?.error?.message || 'Failed to finalize interview.';
      error(msg);
      navigate(`/interviews/${interviewId}`);
    }
  };

  if (isInterviewLoading || !interview) {
    return <PageLoading label="Initializing AI interview environment..." />;
  }

  const formatTimer = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remaining = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${remaining.toString().padStart(2, '0')}`;
  };

  const currentQNum = activeQuestion ? activeQuestion.question_number : interview.current_question;
  const totalQuestions = interview.total_questions;
  const progressPercent = Math.min(100, Math.round((currentQNum / totalQuestions) * 100));

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-20">
      {/* Top Session Status Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-card border border-border p-4 rounded-2xl shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-accent/15 flex items-center justify-center shrink-0">
            <Brain className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h1 className="text-base font-bold text-text-primary">{interview.role}</h1>
            <p className="text-xs text-text-muted capitalize">
              {interview.interview_type.replace('_', ' ')} · {interview.difficulty} difficulty
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex flex-col items-end">
            <span className="text-xs font-semibold text-text-secondary">
              Question {currentQNum} of {totalQuestions}
            </span>
            <div className="w-32 mt-1">
              <ProgressBar value={progressPercent} max={100} size="sm" variant="accent" />
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleCompleteInterview}
            className="text-xs text-text-muted hover:text-error hover:border-error/40"
          >
            End Interview
          </Button>
        </div>
      </div>

      {/* Main Question Display Card */}
      <AnimatePresence mode="wait">
        {activeQuestion ? (
          <motion.div
            key={activeQuestion.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.3 }}
          >
            <Card padding="lg" className="border-accent/30 shadow-card relative overflow-hidden">
              {/* Question metadata chips */}
              <div className="flex items-center justify-between gap-2 mb-4">
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge variant="accent" size="sm">
                    {activeQuestion.topic}
                  </Badge>
                  {activeQuestion.subtopic && (
                    <Badge variant="default" size="sm">
                      {activeQuestion.subtopic}
                    </Badge>
                  )}
                  {activeQuestion.is_follow_up && (
                    <Badge variant="warning" size="sm">
                      ⚡ Adaptive Follow-up
                    </Badge>
                  )}
                </div>

                {/* Read aloud button */}
                <button
                  onClick={handleSpeakQuestion}
                  aria-label="Read question aloud"
                  className={`p-2 rounded-xl border transition-all ${
                    isSpeakingQuestion
                      ? 'border-accent bg-accent/20 text-accent animate-pulse'
                      : 'border-border text-text-muted hover:text-text-primary hover:border-slate-600'
                  }`}
                  title="Read question aloud"
                >
                  {isSpeakingQuestion ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
                </button>
              </div>

              {/* The Question Text */}
              <h2 className="text-xl md:text-2xl font-bold text-text-primary leading-relaxed">
                {activeQuestion.question_text}
              </h2>
            </Card>
          </motion.div>
        ) : (
          <Card padding="lg" className="text-center py-12">
            <Spinner size="md" label="Generating customized interview question..." />
          </Card>
        )}
      </AnimatePresence>

      {/* Answer Workspace */}
      <Card padding="lg" className="space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-text-primary">Your Response</h3>
            <span className="text-xs text-text-muted">
              {inputMode === 'voice' ? '(Spoken Voice Answer)' : '(Written Answer)'}
            </span>
          </div>

          {/* Toggle between Text and Voice */}
          <div className="flex items-center gap-1 bg-slate-900/60 p-1 rounded-xl border border-border">
            <button
              type="button"
              onClick={() => setInputMode('text')}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                inputMode === 'text'
                  ? 'bg-accent text-white shadow-sm'
                  : 'text-text-muted hover:text-text-primary'
              }`}
            >
              Text
            </button>
            <button
              type="button"
              onClick={() => setInputMode('voice')}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                inputMode === 'voice'
                  ? 'bg-accent text-white shadow-sm'
                  : 'text-text-muted hover:text-text-primary'
              }`}
            >
              Voice
            </button>
          </div>
        </div>

        {/* VOICE MODE */}
        {inputMode === 'voice' && (
          <div className="space-y-4 py-2">
            {/* Recording Controls */}
            <div className="flex flex-col items-center justify-center p-8 rounded-2xl bg-slate-900/40 border border-border/80 text-center space-y-4">
              <div className="relative">
                {isRecording && (
                  <span className="absolute -inset-2 rounded-full bg-error/20 animate-ping" />
                )}
                <button
                  type="button"
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={isEvaluating}
                  className={`w-16 h-16 rounded-full flex items-center justify-center transition-all ${
                    isRecording
                      ? 'bg-error text-white shadow-lg shadow-error/30'
                      : 'bg-accent text-white shadow-lg shadow-accent/30 hover:scale-105'
                  }`}
                  aria-label={isRecording ? 'Stop Recording' : 'Start Recording'}
                >
                  {isRecording ? <Square className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
                </button>
              </div>

              <div>
                <p className="text-2xl font-mono font-bold text-text-primary">
                  {formatTimer(recordingSeconds)}
                </p>
                <p className="text-xs text-text-muted mt-1">
                  {isRecording
                    ? 'Listening... Click square to finish speaking'
                    : audioBlob
                    ? 'Recording saved. You can listen back or submit.'
                    : 'Click the mic icon when you are ready to speak'}
                </p>
              </div>

              {/* Audio playback & reset controls */}
              {audioUrl && !isRecording && (
                <div className="flex items-center gap-3 pt-2">
                  <audio src={audioUrl} controls className="h-9 rounded-lg" />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={resetRecording}
                    leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
                  >
                    Re-record
                  </Button>
                </div>
              )}
            </div>

            {/* Live Transcript / Speech Preview */}
            {(liveTranscript || isRecording) && (
              <div className="p-4 rounded-xl bg-slate-900/40 border border-border">
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant="accent" size="sm">Speech Transcription</Badge>
                  {isRecording && <span className="text-xs text-accent animate-pulse">Transcribing live...</span>}
                </div>
                <p className="text-sm text-text-secondary leading-relaxed">
                  {liveTranscript || 'Start speaking to see real-time speech preview...'}
                </p>
              </div>
            )}
          </div>
        )}

        {/* TEXT MODE */}
        {inputMode === 'text' && (
          <div className="space-y-2">
            <textarea
              rows={8}
              value={textAnswer}
              onChange={(e) => setTextAnswer(e.target.value)}
              placeholder="Structure your answer clearly. Discuss core principles, tradeoffs, algorithmic complexity, architectural decisions, and edge cases..."
              disabled={isEvaluating}
              className="w-full bg-background border border-border text-text-primary placeholder:text-text-muted rounded-2xl p-4 text-sm font-sans outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 leading-relaxed resize-y"
            />
            <div className="flex items-center justify-between text-xs text-text-muted px-1">
              <span>{textAnswer.trim().split(/\s+/).filter(Boolean).length} words</span>
              <span>Estimated speak time: ~{Math.ceil(textAnswer.trim().split(/\s+/).filter(Boolean).length / 130)} min</span>
            </div>
          </div>
        )}

        {/* Submission Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-border">
          <span className="text-xs text-text-muted">
            Instant AI evaluation evaluates technical depth, clarity, and reasoning.
          </span>

          <Button
            id="submit-interview-answer-btn"
            size="lg"
            isLoading={isEvaluating}
            onClick={handleSubmitAnswer}
            disabled={isRecording || (!textAnswer.trim() && !audioBlob)}
            rightIcon={<Send className="w-4 h-4" />}
          >
            Submit Answer
          </Button>
        </div>
      </Card>

      {/* Answer Evaluation Instant Feedback Modal */}
      <Modal
        isOpen={showEvaluationModal}
        onClose={handleAdvanceQuestion}
        maxWidth="lg"
        title="Immediate Answer Feedback"
      >
        {latestEvaluation && (
          <div className="space-y-6 pt-2">
            {/* Score header */}
            <div className="flex items-center justify-between bg-card p-4 rounded-2xl border border-border">
              <div>
                <p className="text-xs font-semibold text-text-muted uppercase tracking-wider">Answer Score</p>
                <p className="text-2xl font-bold text-text-primary mt-0.5">
                  {Math.round(latestEvaluation.scores.overall)}%
                </p>
                <p className="text-xs text-text-muted">
                  Technical: {Math.round(latestEvaluation.scores.technical)}% · Communication: {Math.round(latestEvaluation.scores.communication)}%
                </p>
              </div>
              <CircularScore score={Math.round(latestEvaluation.scores.overall)} size={64} strokeWidth={5} />
            </div>

            {/* Strengths & Weaknesses */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                <p className="text-xs font-bold text-emerald-400 mb-2 flex items-center gap-1.5">
                  <CheckCircle className="w-3.5 h-3.5" /> Strengths
                </p>
                <ul className="space-y-1.5 text-xs text-text-secondary">
                  {latestEvaluation.qualitative.strengths.slice(0, 3).map((s, i) => (
                    <li key={i} className="leading-snug">• {s}</li>
                  ))}
                </ul>
              </div>

              <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20">
                <p className="text-xs font-bold text-amber-400 mb-2 flex items-center gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5" /> Areas to Refine
                </p>
                <ul className="space-y-1.5 text-xs text-text-secondary">
                  {latestEvaluation.qualitative.weaknesses.slice(0, 3).map((w, i) => (
                    <li key={i} className="leading-snug">• {w}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Missing concepts */}
            {latestEvaluation.qualitative.missing_concepts.length > 0 && (
              <div className="p-3.5 rounded-xl bg-purple-500/10 border border-purple-500/20">
                <p className="text-xs font-bold text-purple-400 mb-1.5">Missing Technical Concepts:</p>
                <div className="flex flex-wrap gap-1.5">
                  {latestEvaluation.qualitative.missing_concepts.map((concept, i) => (
                    <span key={i} className="px-2 py-0.5 rounded-md bg-purple-500/20 text-[11px] font-medium text-purple-300">
                      {concept}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Continue Button */}
            <div className="pt-2 flex justify-end">
              <Button
                id="modal-next-question-btn"
                onClick={handleAdvanceQuestion}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                {currentQNum >= totalQuestions ? 'View Final Report' : 'Next Question'}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
