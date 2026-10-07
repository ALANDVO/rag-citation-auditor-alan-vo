export type Role = 'viewer' | 'analyst' | 'admin';

export interface UserProfile {
  user_id: string;
  email: string;
  roles: string[];
  is_authenticated: boolean;
  is_demo: boolean;
  csrf_token: string;
}

export interface Project {
  id: number;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface Passage {
  id: number;
  project_id: number;
  passage_id: string;
  title: string;
  content: string;
  url: string;
  chunk_index: number;
  token_count: number;
  created_at: string;
}

export interface Answer {
  id: number;
  project_id: number;
  query: string;
  generated_text: string;
  model_name: string;
  created_at: string;
}

export interface NumericEntity {
  raw_text: string;
  value: number;
  unit: string | null;
  kind: string;
  start_char?: number;
  end_char?: number;
}

export interface ClaimAudit {
  id: number;
  audit_run_id: number;
  sentence_index: number;
  sentence_text: string;
  clean_claim_text: string;
  cited_passage_ids: string[];
  status: 'SUPPORTED' | 'PARTIALLY_SUPPORTED' | 'UNSUPPORTED' | 'UNLINKED_CITATION' | 'NUMERIC_MISMATCH' | string;
  confidence_score: number;
  token_overlap_score: number;
  numeric_entities: NumericEntity[];
  match_details: {
    reason?: string;
    unlinked_citations?: string[];
    valid_citations?: string[];
    discrepancies?: any[];
    overlap_metrics?: {
      containment: number;
      jaccard: number;
      bigram_overlap: number;
      composite_score: number;
    };
  };
  review_status: 'PENDING' | 'VERIFIED_TRUE' | 'FALSE_POSITIVE' | 'HALLUCINATION_CONFIRMED' | 'CORRECTED';
  auditor_notes: string;
  reviewer_user: string;
}

export interface AuditRunSummary {
  id: number;
  answer_id: number;
  project_id: number;
  total_claims: number;
  supported_count: number;
  partially_supported_count: number;
  unsupported_count: number;
  unlinked_count: number;
  numeric_mismatch_count: number;
  faithfulness_score: number;
  citation_precision: number;
  citation_recall: number;
  numeric_accuracy: number;
  status: string;
  created_at: string;
}

export interface AuditRunResponse extends AuditRunSummary {
  claims: ClaimAudit[];
}

export interface ReviewQueueItem {
  id: number;
  claim_id: number;
  audit_run_id: number;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'PENDING' | 'RESOLVED' | 'DISMISSED';
  assigned_to: string;
  resolution_notes: string;
  resolved_at: string | null;
  resolved_by: string;
  claim?: ClaimAudit;
}

export interface AuditLog {
  id: number;
  timestamp: string;
  user_id: string;
  user_email: string;
  user_role: string;
  action: string;
  entity_type: string;
  entity_id: string;
  details: Record<string, any>;
}

export interface LLMAdvisoryResponse {
  claim_id: number;
  advisory_text: string;
  provider: string;
  model: string;
  grounded_evidence: string[];
  is_advisory: boolean;
  notice: string;
}

export interface BenchmarkRunResponse {
  total_samples: number;
  precision: number;
  recall: number;
  f1: number;
  numeric_error_detection_rate: number;
  false_alarm_rate: number;
  baseline_overlap_f1: number;
  execution_time_ms: number;
  failure_cases: Array<{
    sample_id: string;
    kind: string;
    answer: string;
  }>;
}
