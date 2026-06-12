"""
Proposal Routes — FastAPI endpoints for running proposal generation agent swarm workflows.
"""

from fastapi import APIRouter, HTTPException
from schemas.proposal import ProposalGenerationRequest, ProposalGenerationResponse
from agents.workflow import proposal_swarm_graph, get_retrieval_service
from services.chunking_service import process_markdown_pipeline, prepare_for_vector_db
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
        parent_chunks, child_chunks = process_markdown_pipeline(request.rfpText)

        # Format parent chunks into AgentState's expected 'sections' format
        sections = [
            {
                "id": c.id,
                "heading_path": c.section_path,
                "content": c.text,
            }
            for c in parent_chunks
        ]

        # ── Step 2: Index current chunks into Vector DB and BM25 index ──
        retrieval = get_retrieval_service()
        docs_to_index = prepare_for_vector_db(child_chunks)
        collection_name = f"rfp_{request.projectId[:8]}" if request.projectId else "rfp_chunks"
        
        if retrieval.vector_store:
            try:
                retrieval.vector_store.add_documents(collection_name, docs_to_index)
            except Exception as e:
                logger.warning(f"Failed to upsert to Qdrant: {e}")

        if retrieval.bm25_index:
            retrieval.bm25_index.index_documents(docs_to_index, collection_name=collection_name)

        # ── Step 3: Run the Compiled LangGraph Workflow ──
        initial_state = {
            "rfp_text": request.rfpText,
            "sections": sections,
            "collection_name": collection_name,
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
