"""Human evidence review queue and audit resolution endpoints."""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_role, record_audit_log
from app.models.entities import ReviewQueueItem, ClaimAudit, AuditLog, utc_now
from app.models.schemas import (
    ReviewQueueItemResponse,
    ReviewActionRequest,
    AuditLogResponse,
    ClaimAuditResponse
)
from app.api.audits import _serialize_claim

router = APIRouter(prefix="/review", tags=["Human Review Queue"])


@router.get("/queue", response_model=List[ReviewQueueItemResponse])
def get_review_queue(
    status_filter: Optional[str] = Query("PENDING"),
    priority_filter: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("viewer"))
):
    """Retrieves items queued for human evidence inspection and dispute resolution."""
    query = db.query(ReviewQueueItem)
    if status_filter:
        query = query.filter(ReviewQueueItem.status == status_filter)
    if priority_filter:
        query = query.filter(ReviewQueueItem.priority == priority_filter)

    items = query.order_by(
        # Priority order HIGH > MEDIUM > LOW
        ReviewQueueItem.priority.asc(),
        ReviewQueueItem.id.asc()
    ).limit(limit).all()

    result: List[ReviewQueueItemResponse] = []
    for it in items:
        claim_resp = None
        if it.claim:
            claim_resp = _serialize_claim(it.claim)
        result.append(
            ReviewQueueItemResponse(
                id=it.id,
                claim_id=it.claim_id,
                audit_run_id=it.audit_run_id,
                priority=it.priority,
                status=it.status,
                assigned_to=it.assigned_to or "",
                resolution_notes=it.resolution_notes or "",
                resolved_at=it.resolved_at,
                resolved_by=it.resolved_by or "",
                claim=claim_resp
            )
        )
    return result


@router.post("/action", response_model=ClaimAuditResponse)
def resolve_review_item(
    action: ReviewActionRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("analyst"))
):
    """Submits human auditor decision on a flagged claim."""
    claim = db.query(ClaimAudit).filter(ClaimAudit.id == action.claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found.")

    prev_status = claim.review_status
    claim.review_status = action.review_status
    claim.auditor_notes = action.auditor_notes
    claim.reviewer_user = user["user_id"]

    if action.corrected_citation_ids is not None:
        claim.cited_passage_ids = json.dumps(action.corrected_citation_ids)

    # Update associated queue item if present
    q_item = db.query(ReviewQueueItem).filter(ReviewQueueItem.claim_id == claim.id).first()
    if q_item:
        q_item.status = "RESOLVED"
        q_item.resolution_notes = action.auditor_notes
        q_item.resolved_at = utc_now()
        q_item.resolved_by = user["user_id"]

    db.commit()
    db.refresh(claim)

    record_audit_log(
        db,
        user=user,
        action="RESOLVE_REVIEW_CLAIM",
        entity_type="claim_audit",
        entity_id=str(claim.id),
        details={
            "previous_status": prev_status,
            "new_status": claim.review_status,
            "notes": claim.auditor_notes,
            "corrected_citations": action.corrected_citation_ids
        }
    )

    return _serialize_claim(claim)


@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin"))
):
    """Retrieves immutable audit trail for compliance verification."""
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
    result = []
    for l in logs:
        try:
            details_dict = json.loads(l.details)
        except Exception:
            details_dict = {}
        result.append(
            AuditLogResponse(
                id=l.id,
                timestamp=l.timestamp,
                user_id=l.user_id,
                user_email=l.user_email,
                user_role=l.user_role,
                action=l.action,
                entity_type=l.entity_type,
                entity_id=l.entity_id,
                details=details_dict
            )
        )
    return result
