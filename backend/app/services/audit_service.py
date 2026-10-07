"""Orchestration service managing projects, passages, audit runs, and review queues."""
import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.entities import Project, Passage, Answer, AuditRun, ClaimAudit, ReviewQueueItem
from app.models.schemas import PassageCreate, AnswerCreate
from app.services.faithfulness_engine import FaithfulnessEngine
from app.services.llm_client import LLMClient
from app.core.security import record_audit_log


class AuditService:
    @classmethod
    def get_or_create_project(cls, db: Session, name: str = "default-rag-corpus") -> Project:
        proj = db.query(Project).filter(Project.name == name).first()
        if not proj:
            proj = Project(name=name, description="Default RAG document collection workspace.")
            db.add(proj)
            db.commit()
            db.refresh(proj)
        return proj

    @classmethod
    def add_passage(cls, db: Session, project_id: int, p_in: PassageCreate, user: Dict[str, Any]) -> Passage:
        tok_count = len(p_in.content.split())
        p = Passage(project_id=project_id, passage_id=p_in.passage_id, title=p_in.title or f"Passage {p_in.passage_id}",
                    content=p_in.content, url=p_in.url or "", chunk_index=p_in.chunk_index or 0, token_count=tok_count)
        db.add(p)
        db.commit()
        db.refresh(p)
        record_audit_log(db, user, "INGEST_PASSAGE", "passage", p.passage_id, {"project_id": project_id, "title": p.title})
        return p

    @classmethod
    def record_answer(cls, db: Session, project_id: int, a_in: AnswerCreate, user: Dict[str, Any]) -> Answer:
        ans = Answer(project_id=project_id, query=a_in.query, generated_text=a_in.generated_text, model_name=a_in.model_name or "rag-pipeline")
        db.add(ans)
        db.commit()
        db.refresh(ans)
        record_audit_log(db, user, "INGEST_ANSWER", "answer", str(ans.id), {"project_id": project_id, "query": ans.query[:100]})
        return ans

    @classmethod
    def execute_audit(cls, db: Session, answer_id: int, user: Dict[str, Any]) -> AuditRun:
        answer = db.query(Answer).filter(Answer.id == answer_id).first()
        if not answer:
            raise ValueError(f"Answer {answer_id} not found.")

        passages = db.query(Passage).filter(Passage.project_id == answer.project_id).all()
        p_data = [{"passage_id": p.passage_id, "content": p.content} for p in passages]
        res = FaithfulnessEngine.audit_full_answer(answer.generated_text, p_data)

        run = AuditRun(
            answer_id=answer.id, project_id=answer.project_id, total_claims=res["total_claims"],
            supported_count=res["supported_count"], partially_supported_count=res["partially_supported_count"],
            unsupported_count=res["unsupported_count"], unlinked_count=res["unlinked_count"],
            numeric_mismatch_count=res["numeric_mismatch_count"], faithfulness_score=res["faithfulness_score"],
            citation_precision=res["citation_precision"], citation_recall=res["citation_recall"],
            numeric_accuracy=res["numeric_accuracy"], status="COMPLETED"
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        for cd in res["claims"]:
            claim = ClaimAudit(
                audit_run_id=run.id, sentence_index=cd["sentence_index"], sentence_text=cd["sentence_text"],
                clean_claim_text=cd["clean_claim_text"], cited_passage_ids=json.dumps(cd["cited_passage_ids"]),
                status=cd["status"], confidence_score=cd["confidence_score"], token_overlap_score=cd["token_overlap_score"],
                numeric_entities=json.dumps(cd["numeric_entities"]), match_details=json.dumps(cd["match_details"]),
                review_status="PENDING", auditor_notes="", reviewer_user=""
            )
            db.add(claim)
            db.commit()
            db.refresh(claim)

            if cd["status"] in {"UNSUPPORTED", "UNLINKED_CITATION", "NUMERIC_MISMATCH", "PARTIALLY_SUPPORTED"}:
                q_item = ReviewQueueItem(claim_id=claim.id, audit_run_id=run.id, priority=cd["review_priority"], status="PENDING")
                db.add(q_item)

        db.commit()
        db.refresh(run)
        record_audit_log(db, user, "RUN_AUDIT", "audit_run", str(run.id), {"total_claims": run.total_claims, "score": run.faithfulness_score})
        return run

    @classmethod
    async def get_advisory_explanation(cls, db: Session, claim_id: int, user: Dict[str, Any]) -> Dict[str, Any]:
        claim = db.query(ClaimAudit).filter(ClaimAudit.id == claim_id).first()
        if not claim: raise ValueError(f"Claim {claim_id} not found.")

        run = db.query(AuditRun).filter(AuditRun.id == claim.audit_run_id).first()
        ans = db.query(Answer).filter(Answer.id == run.answer_id).first()
        passages = db.query(Passage).filter(Passage.project_id == ans.project_id).all()

        try: cids = set(json.loads(claim.cited_passage_ids))
        except Exception: cids = set()

        rel_p = [p.content for p in passages if p.passage_id in cids] or [p.content for p in passages[:3]]
        try: mdet = json.loads(claim.match_details)
        except Exception: mdet = {}

        explanation = await LLMClient.generate_advisory_explanation(claim.clean_claim_text, rel_p, claim.status, mdet.get("discrepancies", []))
        record_audit_log(db, user, "GENERATE_ADVISORY", "claim_audit", str(claim_id), {"provider": explanation.get("provider")})
        return explanation
