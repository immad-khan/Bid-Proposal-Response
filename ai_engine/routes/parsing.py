"""
Parsing Routes — FastAPI endpoints for document layout parsing and chunking.
"""

from fastapi import APIRouter, HTTPException
from schemas.rfp import RFPParseRequest
from services.parser_service import parse_azure_blob_hybrid
from services.chunking_service import process_markdown_pipeline, prepare_for_vector_db
from services.extractor_service import ExtractionService
import logging
from pydantic import BaseModel

class ExtractionRequest(BaseModel):
    rfpText: str

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/parsing", tags=["parsing"])


@router.post("/parse")
async def parse_document(request: RFPParseRequest):
    """
    Parse an RFP document from Azure Blob storage.
    Runs the hybrid parser (Docling + PDFPlumber) and returns
    hierarchical parent-child sections ready for vector storage.
    """
    try:
        logger.info(f"Parsing route triggered for job {request.jobId} | URL: {request.blobUrl}")

        # Step 1: Parse PDF from Azure Blob
        raw_markdown = await parse_azure_blob_hybrid(request.blobUrl)

        # Step 2: Split → Chunk → Contextual Prepend
        parent_chunks, child_chunks = process_markdown_pipeline(raw_markdown)

        # Step 3: Format for response
        vector_db_docs = prepare_for_vector_db(child_chunks)

        return {
            "jobId": request.jobId,
            "status": "parsed",
            "parent_sections_count": len(parent_chunks),
            "child_chunks_count": len(child_chunks),
            "sections": [
                {
                    "id": c.id,
                    "heading_path": c.section_path,
                    "content_preview": c.text[:200],
                    "token_count": c.token_count,
                }
                for c in parent_chunks
            ],
        }
    except Exception as e:
        logger.error(f"Error during parsing endpoint execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract")
async def extract_intelligence(request: ExtractionRequest):
    """
    Node 2.0: NER & Schema Extraction
    Extracts key dates, verbs, KPIs, budget, and compliance standards.
    Returns the structured JSON preview.
    """
    try:
        extractor = ExtractionService()
        result = extractor.extract_intelligence(request.rfpText)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Extraction route failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
