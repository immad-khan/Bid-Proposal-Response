"""
Parsing Routes — FastAPI endpoints for document layout parsing and chunking.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from schemas.rfp import RFPParseRequest
from services.parser_service import parse_azure_blob_hybrid
from services.chunking_service import create_parent_child_chunks
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/parsing", tags=["parsing"])


@app_router_post_route := "/parse"
@router.post(app_router_post_route)
async def parse_document(request: RFPParseRequest):
    """
    Parse an RFP document from Azure Blob storage.
    Runs the hybrid parser and returns hierarchical parent-child sections.
    """
    try:
        logger.info(f"Parsing route triggered for job {request.jobId} | URL: {request.blobUrl}")
        raw_markdown = await parse_azure_blob_hybrid(request.blobUrl)
        document_hierarchy = create_parent_child_chunks(raw_markdown)

        return {
            "jobId": request.jobId,
            "status": "parsed",
            "parent_sections_count": len(document_hierarchy),
            "sections": document_hierarchy
        }
    except Exception as e:
        logger.error(f"Error during parsing endpoint execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))
