/**
 * AI Interview Platform — TypeScript Type Definitions
 * Strictly synchronized with backend Pydantic schemas (v1 API).
 */

// ==========================================
// 1. API Envelope & Common Types
// ==========================================

export interface ErrorDetails {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface APIResponse<T> {
  success: boolean;
  data: T;
  request_id: string;
  message?: string;
  error?: ErrorDetails | null;
}

export interface ErrorResponse {
  success: false;
  error: ErrorDetails;
  request_id: string;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded';
  version: string;
  environment: string;
  services: Record<string, string>;
}

// ==========================================
// 2. Auth & User Types
// ==========================================

export type UserRole = 'candidate' | 'interviewer' | 'admin';

export interface UserResponse {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  role?: UserRole;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserResponse;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface UserUpdate {
  name?: string;
  email?: string;
}

// ==========================================
// 3. Interview Types
// ==========================================

export type InterviewType =
  | 'general'
  | 'technical'
  | 'hr'
  | 'company_style'
  | 'topic_specific'
  | 'resume_based'
  | 'document_based'
  | 'mixed';

export type InterviewDifficulty = 'beginner' | 'intermediate' | 'advanced';

export type InterviewMode = 'voice' | 'text';

export type InterviewStatus = 'created' | 'in_progress' | 'completed' | 'abandoned';

export interface InterviewCreateRequest {
  role: string;
  interview_type?: InterviewType;
  difficulty?: InterviewDifficulty;
  topics: string[];
  question_count?: number;
  mode?: InterviewMode;
  company_style?: string;
  document_ids?: string[];
}

export interface InterviewQuestionSummary {
  id: string;
  question_number: int_or_number;
  topic: string;
  subtopic?: string | null;
  difficulty: string;
  question_text: string;
  is_follow_up: boolean;
  created_at: string;
}

type int_or_number = number;

export interface InterviewResponse {
  id: string;
  user_id: string;
  role: string;
  interview_type: InterviewType | string;
  difficulty: InterviewDifficulty | string;
  status: InterviewStatus | string;
  total_questions: number;
  current_question: number;
  started_at: string | null;
  completed_at: string | null;
  configuration: {
    topics?: string[];
    mode?: InterviewMode;
    company_style?: string | null;
    document_ids?: string[];
    [key: string]: unknown;
  };
  overall_score?: number | null;
  created_at: string;
}

export interface InterviewDetailResponse extends InterviewResponse {
  questions: InterviewQuestionSummary[];
}

export interface InterviewListResponse {
  items: InterviewResponse[];
  total: number;
  page: number;
  page_size: number;
}

// ==========================================
// 4. Question Types
// ==========================================

export interface QuestionResponse {
  id: string;
  interview_id: string;
  question_number: number;
  topic: string;
  subtopic?: string | null;
  difficulty: string;
  question_text: string;
  is_follow_up: boolean;
  created_at: string;
}

// ==========================================
// 5. Answer Submission Types
// ==========================================

export interface TextAnswerSubmission {
  question_id: string;
  text_answer: string;
  duration_seconds?: number;
}

export interface AnswerResponse {
  id: string;
  question_id: string;
  user_id: string;
  text_answer: string | null;
  audio_file_url: string | null;
  transcript: string | null;
  duration_seconds: number | null;
  created_at: string;
}

// ==========================================
// 6. Evaluation & Feedback Types
// ==========================================

export interface EvaluationResponse {
  evaluation_id: string;
  answer_id: string;
  scores: {
    technical: number;
    accuracy: number;
    completeness: number;
    reasoning: number;
    grammar: number;
    communication: number;
    fluency: number;
    clarity: number;
    confidence: number;
    overall: number;
  };
  speech_metrics: {
    filler_word_count: number;
    pause_count: number;
    speaking_rate_wpm: number;
  };
  qualitative: {
    strengths: string[];
    weaknesses: string[];
    missing_concepts: string[];
    feedback: Record<string, unknown>;
  };
  meta: {
    evaluator_version: string;
    created_at: string | null;
  };
}

export interface InterviewFeedbackResponse {
  interview_id: string;
  overall_score: number;
  average_technical_score: number;
  average_communication_score: number;
  average_grammar_score: number;
  average_fluency_score: number;
  average_confidence_score: number;
  total_questions_evaluated: number;
  strengths_summary: string[];
  weaknesses_summary: string[];
  missing_concepts_summary: string[];
  created_at: string | null;
}

export interface TopicBreakdownItem {
  topic: string;
  question_count: number;
  average_score: number;
  average_overall: number;
}

export interface LearningRecommendationItem {
  topic: string;
  priority: 'high' | 'medium' | 'low';
  reason: string;
  suggested_action: string;
  resources?: string[];
}

export interface UserPerformanceProfile {
  summary: {
    total_interviews: number;
    total_evaluations: number;
    avg_technical: number;
    avg_communication: number;
    avg_grammar: number;
    avg_fluency: number;
    avg_confidence: number;
    avg_overall: number;
  };
  topic_breakdown: TopicBreakdownItem[];
  weak_topics: TopicBreakdownItem[];
  learning_recommendations: LearningRecommendationItem[];
  score_trend: Array<{ date: string; average_score: number }>;
}

// ==========================================
// 7. Documents & RAG Types
// ==========================================

export type DocumentProcessingStatus = 'uploaded' | 'processing' | 'ready' | 'failed';

export interface DocumentItem {
  document_id: string;
  title: string;
  description: string;
  file_type: string;
  file_size: number;
  status: DocumentProcessingStatus;
  chunk_count: number;
  created_at: string | null;
}

export interface DocumentListResponse {
  documents: DocumentItem[];
  total: number;
}

export interface DocumentUploadResponse {
  document_id: string;
  title: string;
  status: string;
  message: string;
}

// ==========================================
// 8. Speech & Audio Types
// ==========================================

export interface SpeechTranscriptionResponse {
  transcript: string;
  confidence: number;
  character_count: number;
  word_count: number;
  language_hint: string;
}

export interface SpeechFeatures {
  word_count: number;
  speaking_rate_wpm: number;
  filler_word_count: number;
  filler_words_found: string[];
  pause_count: number;
  estimated_fluency_score: number;
}

export interface SpeechFeaturesResponse {
  speech_features: SpeechFeatures;
  confidence_estimate: number;
  duration_seconds: number;
}
