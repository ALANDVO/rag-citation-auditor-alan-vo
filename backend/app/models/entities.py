"""SQLAlchemy database entities for RAG Citation Auditor."""
import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False, index=True)
    description = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    passages = relationship("Passage", back_populates="project", cascade="all, delete-orphan")
    answers = relationship("Answer", back_populates="project", cascade="all, delete-orphan")


class Passage(Base):
    __tablename__ = "passages"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    passage_id = Column(String(64), nullable=False, index=True)
    title = Column(String(256), default="")
    content = Column(Text, nullable=False)
    url = Column(String(512), default="")
    chunk_index = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    project = relationship("Project", back_populates="passages")
    __table_args__ = (Index("ix_project_passage_id", "project_id", "passage_id"),)


class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    generated_text = Column(Text, nullable=False)
    model_name = Column(String(128), default="unknown-model")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    project = relationship("Project", back_populates="answers")
    audit_runs = relationship("AuditRun", back_populates="answer", cascade="all, delete-orphan")


class AuditRun(Base):
    __tablename__ = "audit_runs"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    answer_id = Column(Integer, ForeignKey("answers.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    total_claims = Column(Integer, default=0, nullable=False)
    supported_count = Column(Integer, default=0, nullable=False)
    partially_supported_count = Column(Integer, default=0, nullable=False)
    unsupported_count = Column(Integer, default=0, nullable=False)
    unlinked_count = Column(Integer, default=0, nullable=False)
    numeric_mismatch_count = Column(Integer, default=0, nullable=False)
    faithfulness_score = Column(Float, default=0.0, nullable=False)
    citation_precision = Column(Float, default=0.0, nullable=False)
    citation_recall = Column(Float, default=0.0, nullable=False)
    numeric_accuracy = Column(Float, default=0.0, nullable=False)
    status = Column(String(32), default="COMPLETED", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    answer = relationship("Answer", back_populates="audit_runs")
    claims = relationship("ClaimAudit", back_populates="audit_run", cascade="all, delete-orphan")


class ClaimAudit(Base):
    __tablename__ = "claim_audits"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    audit_run_id = Column(Integer, ForeignKey("audit_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    sentence_index = Column(Integer, nullable=False)
    sentence_text = Column(Text, nullable=False)
    clean_claim_text = Column(Text, nullable=False)
    cited_passage_ids = Column(Text, default="[]", nullable=False)
    status = Column(String(32), nullable=False)
    confidence_score = Column(Float, default=0.0, nullable=False)
    token_overlap_score = Column(Float, default=0.0, nullable=False)
    numeric_entities = Column(Text, default="[]", nullable=False)
    match_details = Column(Text, default="{}", nullable=False)
    review_status = Column(String(32), default="PENDING", nullable=False)
    auditor_notes = Column(Text, default="")
    reviewer_user = Column(String(128), default="")

    audit_run = relationship("AuditRun", back_populates="claims")
    review_queue_item = relationship("ReviewQueueItem", back_populates="claim", uselist=False, cascade="all, delete-orphan")


class ReviewQueueItem(Base):
    __tablename__ = "review_queue_items"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    claim_id = Column(Integer, ForeignKey("claim_audits.id", ondelete="CASCADE"), unique=True, nullable=False)
    audit_run_id = Column(Integer, ForeignKey("audit_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    priority = Column(String(16), default="MEDIUM", nullable=False)
    status = Column(String(16), default="PENDING", nullable=False)
    assigned_to = Column(String(128), default="")
    resolution_notes = Column(Text, default="")
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(128), default="")

    claim = relationship("ClaimAudit", back_populates="review_queue_item")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    user_id = Column(String(128), nullable=False)
    user_email = Column(String(256), nullable=False)
    user_role = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False)
    details = Column(Text, default="{}", nullable=False)


class SessionRecord(Base):
    __tablename__ = "sessions"
    session_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(128), nullable=False)
    email = Column(String(256), nullable=False)
    roles = Column(Text, default="[]", nullable=False)
    csrf_token = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
