"""
Compliance Routes — FastAPI endpoints for Neo4j compliance matrix management
and Go/No-Go bid evaluations.
"""

from fastapi import APIRouter, HTTPException
from schemas.compliance import (
    RequirementCreateSchema,
    ComplianceLinkSchema,
    GoNoGoEvaluateSchema,
    GoNoGoResponseSchema,
)
from services.compliance_matrix import ComplianceMatrixService
from services.go_nogo_engine import GoNoGoEngine
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/compliance", tags=["compliance"])

# Initialize services
try:
    neo4j_service = ComplianceMatrixService()
except Exception as e:
    logger.warning(f"Neo4j client could not be initialized during route loading: {e}. Fallback logic will be utilized.")
    neo4j_service = None

gonogo_engine = GoNoGoEngine()


@router.post("/requirement")
async def add_requirement(req: RequirementCreateSchema):
    """Create a new requirement node in the Neo4j compliance matrix."""
    if not neo4j_service:
        raise HTTPException(status_code=503, detail="Neo4j service unavailable")
    try:
        neo4j_service.create_requirement_node(
            requirement_id=req.requirementId,
            section_path=req.sectionPath,
            description=req.description,
            is_mandatory=req.isMandatory,
            page_ref=req.pageRef,
        )
        return {"status": "success", "message": f"Requirement {req.requirementId} added."}
    except Exception as e:
        logger.error(f"Failed to add requirement: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/link")
async def link_compliance(link: ComplianceLinkSchema):
    """Link a proposal section to a requirement with a status and evidence."""
    if not neo4j_service:
        raise HTTPException(status_code=503, detail="Neo4j service unavailable")
    try:
        neo4j_service.link_compliance(
            proposal_section_id=link.proposalSectionId,
            requirement_id=link.requirementId,
            status=link.status,
            evidence=link.evidence,
            score=link.score,
        )
        return {"status": "success", "message": "Compliance link created."}
    except Exception as e:
        logger.error(f"Failed to link compliance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matrix")
async def get_matrix():
    """Retrieve the entire compliance matrix mapping from the graph."""
    if not neo4j_service:
        raise HTTPException(status_code=503, detail="Neo4j service unavailable")
    try:
        return neo4j_service.get_compliance_matrix()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_summary():
    """Retrieve aggregated compliance statistics and gaps."""
    if not neo4j_service:
        raise HTTPException(status_code=503, detail="Neo4j service unavailable")
    try:
        summary = neo4j_service.get_compliance_summary()
        gaps = neo4j_service.get_missing_requirements()
        return {
            "summary": summary,
            "missing_requirements": gaps
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate-bid", response_model=GoNoGoResponseSchema)
async def evaluate_bid(data: GoNoGoEvaluateSchema):
    """Evaluate RFP attributes and generate a Go/No-Go classification decision."""
    try:
        features = {
            "capability_score": data.capability_score,
            "budget_alignment": data.budget_alignment,
            "timeline_feasibility": data.timeline_feasibility,
            "past_win_rate": data.past_win_rate,
            "competitive_intensity": data.competitive_intensity,
            "strategic_value": data.strategic_value,
        }
        evaluation = gonogo_engine.evaluate_bid(features)
        return evaluation
    except Exception as e:
        logger.error(f"Go/No-Go evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import FileResponse

@router.get("/export")
async def export_matrix():
    """6.1 Build Matrix: Export the compliance matrix to a CSV file."""
    if not neo4j_service:
        raise HTTPException(status_code=503, detail="Neo4j service unavailable")
    try:
        filepath = neo4j_service.export_to_csv()
        return FileResponse(filepath, media_type='text/csv', filename="compliance_matrix.csv")
    except Exception as e:
        logger.error(f"Failed to export CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))
