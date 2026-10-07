"""Audits, Passages and Answers API endpoints with role-based authorization."""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_role, record_audit_log
from app.models.entities import Project, Passage, Answer, AuditRun, ClaimAudit
from app.models.schemas import (
    ProjectCreate, ProjectResponse, PassageCreate, PassageResponse,
    AnswerCreate, AnswerResponse, AuditRunResponse, AuditRunSummary,
    ClaimAuditResponse, LLMAdvisoryResponse
)
from app.services.audit_service import AuditService
from app.services.export_service import ExportService

router = APIRouter(prefix="/audits", tags=["Audits & Ingestion"])


def _serialize_claim(c: ClaimAudit) -> ClaimAuditResponse:
    return ClaimAuditResponse(
        id=c.id, audit_run_id=c.audit_run_id, sentence_index=c.sentence_index, sentence_text=c.sentence_text,
        clean_claim_text=c.clean_claim_text, cited_passage_ids=json.loads(c.cited_passage_ids) if c.cited_passage_ids else [],
        status=c.status, confidence_score=c.confidence_score, token_overlap_score=c.token_overlap_score,
        numeric_entities=json.loads(c.numeric_entities) if c.numeric_entities else [],
        match_details=json.loads(c.match_details) if c.match_details else {},
        review_status=c.review_status, auditor_notes=c.auditor_notes or "", reviewer_user=c.reviewer_user or ""
    )


@router.post("/projects", response_model=ProjectResponse)
def create_project(p_in: ProjectCreate, db: Session = Depends(get_db), user: dict = Depends(require_role("analyst"))):
    existing = db.query(Project).filter(Project.name == p_in.name).first()
    if existing: return existing
    proj = Project(name=p_in.name, description=p_in.description or "")
    db.add(proj); db.commit(); db.refresh(proj)
    record_audit_log(db, user, "CREATE_PROJECT", "project", str(proj.id), {"name": proj.name})
    return proj


@router.get("/projects", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db), user: dict = Depends(require_role("viewer"))):
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.post("/passages", response_model=PassageResponse)
def ingest_passage(p_in: PassageCreate, project_id: Optional[int] = Query(None), db: Session = Depends(get_db), user: dict = Depends(require_role("analyst"))):
    if not project_id: project_id = AuditService.get_or_create_project(db).id
    return AuditService.add_passage(db, project_id, p_in, user)


@router.get("/passages", response_model=List[PassageResponse])
def list_passages(project_id: Optional[int] = Query(None), limit: int = Query(50), offset: int = Query(0), db: Session = Depends(get_db), user: dict = Depends(require_role("viewer"))):
    q = db.query(Passage)
    if project_id: q = q.filter(Passage.project_id == project_id)
    return q.order_by(Passage.id.desc()).offset(offset).limit(limit).all()


@router.post("/answers", response_model=AnswerResponse)
def ingest_answer(a_in: AnswerCreate, project_id: Optional[int] = Query(None), db: Session = Depends(get_db), user: dict = Depends(require_role("analyst"))):
    if not project_id: project_id = AuditService.get_or_create_project(db).id
    return AuditService.record_answer(db, project_id, a_in, user)


@router.get("/answers", response_model=List[AnswerResponse])
def list_answers(project_id: Optional[int] = Query(None), limit: int = Query(50), db: Session = Depends(get_db), user: dict = Depends(require_role("viewer"))):
    q = db.query(Answer)
    if project_id: q = q.filter(Answer.project_id == project_id)
    return q.order_by(Answer.id.desc()).limit(limit).all()


@router.post("/run", response_model=AuditRunResponse)
def run_audit(answer_id: int = Query(...), db: Session = Depends(get_db), user: dict = Depends(require_role("analyst"))):
    try: run = AuditService.execute_audit(db, answer_id, user)
    except ValueError as e: raise HTTPException(status_code=404, detail=str(e))
    claims = db.query(ClaimAudit).filter(ClaimAudit.audit_run_id == run.id).order_by(ClaimAudit.sentence_index.asc()).all()
    resp = AuditRunSummary.model_validate(run).model_dump()
    resp["claims"] = [_serialize_claim(c) for c in claims]
    return AuditRunResponse(**resp)


@router.get("/runs", response_model=List[AuditRunSummary])
def list_audit_runs(project_id: Optional[int] = Query(None), limit: int = Query(50), db: Session = Depends(get_db), user: dict = Depends(require_role("viewer"))):
    q = db.query(AuditRun)
    if project_id: q = q.filter(AuditRun.project_id == project_id)
    return q.order_by(AuditRun.id.desc()).limit(limit).all()


@router.get("/runs/{run_id}", response_model=AuditRunResponse)
def get_audit_run(run_id: int, db: Session = Depends(get_db), user: dict = Depends(require_role("viewer"))):
    run = db.query(AuditRun).filter(AuditRun.id == run_id).first()
    if not run: raise HTTPException(status_code=404, detail="Audit run not found.")
    claims = db.query(ClaimAudit).filter(ClaimAudit.audit_run_id == run.id).order_by(ClaimAudit.sentence_index.asc()).all()
    resp = AuditRunSummary.model_validate(run).model_dump()
    resp["claims"] = [_serialize_claim(c) for c in claims]
    return AuditRunResponse(**resp)


@router.post("/claims/{claim_id}/advisory", response_model=LLMAdvisoryResponse)
async def generate_claim_advisory(claim_id: int, db: Session = Depends(get_db), user: dict = Depends(require_role("analyst"))):
    try:
        res = await AuditService.get_advisory_explanation(db, claim_id, user)
        return LLMAdvisoryResponse(claim_id=claim_id, advisory_text=res["advisory_text"], provider=res.get("provider", "unknown"),
                                   model=res.get("model", "unknown"), grounded_evidence=res.get("grounded_evidence", []), is_advisory=True)
    except ValueError as e: raise HTTPException(status_code=404, detail=str(e))


@router.get("/runs/{run_id}/export")
def export_audit_run(run_id: int, format: str = Query("json", pattern="^(json|markdown|csv)$"), db: Session = Depends(get_db), user: dict = Depends(require_role("viewer"))):
    run = db.query(AuditRun).filter(AuditRun.id == run_id).first()
    if not run: raise HTTPException(status_code=404, detail="Audit run not found.")
    claims = db.query(ClaimAudit).filter(ClaimAudit.audit_run_id == run.id).order_by(ClaimAudit.sentence_index.asc()).all()
    resp = AuditRunSummary.model_validate(run).model_dump()
    resp["claims"] = [_serialize_claim(c).model_dump() for c in claims]

    if format == "markdown": return Response(content=ExportService.to_markdown(resp), media_type="text/markdown", headers={"Content-Disposition": f"attachment; filename=audit-{run_id}.md"})
    elif format == "csv": return Response(content=ExportService.to_csv(resp), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=audit-{run_id}.csv"})
    return Response(content=ExportService.to_json(resp), media_type="application/json", headers={"Content-Disposition": f"attachment; filename=audit-{run_id}.json"})
