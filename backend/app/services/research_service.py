from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging
from backend.app.models.research_session import ResearchSession
from backend.app.models.source import Source
from backend.app.models.evidence import EvidenceItem
from backend.app.models.finding import Finding, FindingEvidence
from backend.app.models.recommendation import Recommendation
from backend.app.schemas.research_session import ResearchSessionCreate
from backend.app.ai.workflow import research_graph

logger = logging.getLogger(__name__)

class ResearchService:
    @staticmethod
    def create_session(db: Session, session_in: ResearchSessionCreate) -> ResearchSession:
        new_session = ResearchSession(
            research_question=session_in.question,
            organization_id=session_in.organization_id,
            status="pending"
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session

    @staticmethod
    def get_session(db: Session, session_id: int) -> ResearchSession | None:
        return db.query(ResearchSession).filter(ResearchSession.id == session_id).first()

    @staticmethod
    def get_sessions(db: Session, skip: int = 0, limit: int = 100) -> list[ResearchSession]:
        return db.query(ResearchSession).order_by(ResearchSession.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def delete_session(db: Session, session_id: int) -> bool:
        session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
        if not session:
            return False
            
        db.query(Source).filter(Source.session_id == session_id).delete()
        db.query(EvidenceItem).filter(EvidenceItem.session_id == session_id).delete()
        findings = db.query(Finding).filter(Finding.session_id == session_id).all()
        for f in findings:
            db.query(FindingEvidence).filter(FindingEvidence.finding_id == f.id).delete()
        db.query(Finding).filter(Finding.session_id == session_id).delete()
        db.query(Recommendation).filter(Recommendation.session_id == session_id).delete()
        
        db.delete(session)
        db.commit()
        return True

    @staticmethod
    def execute_workflow(db: Session, session_id: int):
        session = db.query(ResearchSession).get(session_id)
        if not session: return

        session.status = "running"
        db.commit()

        state = {
            "session_id": session_id,
            "research_question": session.research_question,
            "search_queries": [],
            "sources": [],
            "retrieved_chunks": [],
            "evidence": [],
            "findings": [],
            "recommendations": [],
            "errors": [],
            "current_step": "init"
        }

        try:
            logger.info(f"Executing workflow for session {session_id}")
            final_state = research_graph.invoke(state)

            temp_to_real_source = {}
            for s in final_state.get("sources", []):
                new_source = Source(
                    session_id=session_id,
                    title=s["title"],
                    url=s["url"],
                    source_type=s["source_type"],
                    publisher=s["publisher"],
                    content_hash=s["url"],
                    retrieved_at=datetime.fromisoformat(s["retrieved_at"]) if isinstance(s["retrieved_at"], str) else s["retrieved_at"]
                )
                db.add(new_source)
                db.flush()
                temp_to_real_source[s["temp_id"]] = new_source.id

            temp_to_real_evidence = {}
            for e in final_state.get("evidence", []):
                real_source_id = temp_to_real_source.get(e["source_temp_id"])
                if not real_source_id: continue
                new_ev = EvidenceItem(
                    source_id=real_source_id,
                    session_id=session_id,
                    text=e["claim"],
                    evidence_type=e["evidence_type"],
                    relevance_score=e["relevance_score"]
                )
                db.add(new_ev)
                db.flush()
                temp_to_real_evidence[e["temp_id"]] = new_ev.id

            for f in final_state.get("findings", []):
                new_finding = Finding(
                    session_id=session_id,
                    statement=f["statement"],
                    confidence=f["confidence"]
                )
                db.add(new_finding)
                db.flush()

                for link in f.get("evidence_links", []):
                    real_ev_id = temp_to_real_evidence.get(link["evidence_temp_id"])
                    if real_ev_id:
                        db.add(FindingEvidence(
                            finding_id=new_finding.id,
                            evidence_id=real_ev_id,
                            relationship_type=link["relationship_type"]
                        ))

            for r in final_state.get("recommendations", []):
                new_rec = Recommendation(
                    session_id=session_id,
                    recommendation=r["recommendation"],
                    rationale=r["rationale"],
                    confidence=r["confidence"]
                )
                db.add(new_rec)

            if final_state.get("errors"):
                session.error_message = "; ".join(final_state["errors"])
                session.status = "failed" if not final_state.get("recommendations") else "completed"
            else:
                session.status = "completed"

            session.completed_at = datetime.now(timezone.utc)
            db.commit()

        except Exception as e:
            session.status = "failed"
            session.error_message = str(e)
            db.commit()
            logger.error(f"Workflow execution failed: {e}")
