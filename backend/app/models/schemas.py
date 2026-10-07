"""Pydantic request and response schemas for validation and API serialization."""
import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = Field(default="", max_length=1000)


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


class PassageCreate(BaseModel):
    passage_id: str = Field(..., min_length=1, max_length=64)
    title: Optional[str] = Field(default="", max_length=256)
    content: str = Field(..., min_length=1)
    url: Optional[str] = Field(default="", max_length=512)
    chunk_index: Optional[int] = Field(default=0, ge=0)


class PassageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    passage_id: str
    title: str
    content: str
    url: str
    chunk_index: int
    token_count: int
    created_at: datetime.datetime


class AnswerCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    query: str = Field(..., min_length=1)
    generated_text: str = Field(..., min_length=1)
    model_name: Optional[str] = Field(default="unknown-model", max_length=128)


class AnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    id: int
    project_id: int
    query: str
    generated_text: str
    model_name: str
    created_at: datetime.datetime


class ClaimAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    audit_run_id: int
    sentence_index: int
    sentence_text: str
    clean_claim_text: str
    cited_passage_ids: List[str]
    status: str
    confidence_score: float
    token_overlap_score: float
    numeric_entities: List[Dict[str, Any]]
    match_details: Dict[str, Any]
    review_status: str
    auditor_notes: str
    reviewer_user: str


class AuditRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    answer_id: int
    project_id: int
    total_claims: int
    supported_count: int
    partially_supported_count: int
    unsupported_count: int
    unlinked_count: int
    numeric_mismatch_count: int
    faithfulness_score: float
    citation_precision: float
    citation_recall: float
    numeric_accuracy: float
    status: str
    created_at: datetime.datetime


class AuditRunResponse(AuditRunSummary):
    claims: List[ClaimAuditResponse] = []


class ReviewQueueItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    claim_id: int
    audit_run_id: int
    priority: str
    status: str
    assigned_to: str
    resolution_notes: str
    resolved_at: Optional[datetime.datetime]
    resolved_by: str
    claim: Optional[ClaimAuditResponse] = None


class ReviewActionRequest(BaseModel):
    claim_id: int
    review_status: str = Field(..., pattern="^(VERIFIED_TRUE|FALSE_POSITIVE|HALLUCINATION_CONFIRMED|CORRECTED)$")
    auditor_notes: str = Field(..., min_length=1, max_length=2000)
    corrected_citation_ids: Optional[List[str]] = None


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    timestamp: datetime.datetime
    user_id: str
    user_email: str
    user_role: str
    action: str
    entity_type: str
    entity_id: str
    details: Dict[str, Any]


class LLMAdvisoryResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    claim_id: int
    advisory_text: str
    provider: str
    model: str
    grounded_evidence: List[str]
    is_advisory: bool = True
    notice: str = "This analysis is advisory and grounded in ingested passages."


class BenchmarkRunResponse(BaseModel):
    total_samples: int
    precision: float
    recall: float
    f1: float
    numeric_error_detection_rate: float
    false_alarm_rate: float
    baseline_overlap_f1: float
    execution_time_ms: float
    failure_cases: List[Dict[str, Any]]


class UserProfile(BaseModel):
    user_id: str
    email: str
    roles: List[str]
    is_authenticated: bool
    is_demo: bool = False
    csrf_token: str = ""


class DemoLoginRequest(BaseModel):
    role: str = Field(default="analyst", pattern="^(viewer|analyst|admin)$")
