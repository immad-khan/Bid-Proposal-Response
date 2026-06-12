"""
Proposal Routes — FastAPI endpoints for running proposal generation agent swarm workflows.
"""

from fastapi import APIRouter, HTTPException
from schemas.proposal import ProposalGenerationRequest, ProposalGenerationResponse
from agents.workflow import proposal_swarm_graph, get_retrieval_service
from services.chunking_service import create_parent_child_chunks
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/proposal", tags=["proposal"])


@router.post("/generate", response_model=ProposalGenerationResponse)
async def generate_proposal(request: ProposalGenerationRequest):
    """
    Triggers the multi-agent proposal generation workflow using LangGraph.
    Runs planning, drafting, gatekeeper reviews, and judge scoring sequentially.
    """
    try:
        logger.info(f"Proposal generation triggered for project: {request.projectId}")

        # ── Step 1: Chunk the RFP content into parent-child blocks ──
        logger.info("ProposalRouter: Chunking input RFP text...")
        chunks = create_parent_child_chunks(request.rfpText)
        
        # Format chunks into AgentState's expected 'sections' format
        # Each parent chunk acts as a section.
        sections = []
        for i, parent_chunk in enumerate(chunks):
            sections.append({
                "id": f"sec_{i}",
                "heading_path": [parent_chunk.get("section_heading", f"Section {i+1}")],
                "content": parent_chunk.get("text_for_embedding", "")
            })

        # ── Step 2: Index current chunks into the in-memory BM25 index ──
        retrieval = get_retrieval_service()
        if retrieval.bm25_index:
            # We map chunk records to BM25 expected dictionary form
            bm25_docs = []
            for sec in sections:
                bm25_docs.append({
                    "id": sec["id"],
                    "text_for_embedding": sec["content"],
                    "original_text": sec["content"],
                    "metadata": {"section_path": sec["heading_path"][0]}
                })
            retrieval.bm25_index.index_documents(bm25_docs)

        # ── Step 3: Run the Compiled LangGraph Workflow ──
        initial_state = {
            "rfp_text": request.rfpText,
            "sections": sections,
            "plan": {},
            "drafts": {},
            "reviews": [],
            "approved": False,
            "status": "Starting pipeline"
        }

        logger.info("ProposalRouter: Invoking LangGraph agent swarm...")
        final_state = proposal_swarm_graph.invoke(initial_state)
        logger.info("ProposalRouter: LangGraph execution finished.")

        # Gather reviews
        reviews = final_state.get("reviews", [])
        judge_review = next((r for r in reviews if r.get("step") == "llm_judge"), {})
        
        draft_previews = {
            req_id: text[:200] + "..." if len(text) > 200 else text
            for req_id, text in final_state.get("drafts", {}).items()
        }

        response = ProposalGenerationResponse(
            status="completed",
            approved=final_state.get("approved", False),
            overall_score=judge_review.get("overall_score", 0.0),
            sections_drafted=len(final_state.get("drafts", {})),
            draft_previews=draft_previews,
            compliance_issues_count=judge_review.get("issues_found", 0)
        )

        return response

    except Exception as e:
        logger.error(f"Proposal generation endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
