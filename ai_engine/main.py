from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Core pipeline imports
from services.chunking_service import process_markdown_pipeline, prepare_for_vector_db
from services.parser_service import parse_azure_blob_hybrid
from routes import parsing_router, compliance_router, proposal_router
from routes.evaluate_rfp import router as evaluate_rfp_router

# Lazy imports for heavy AI services (loaded on first job, not at startup)
_vector_store = None
_bm25_index = None

def _get_vector_store():
    global _vector_store
    if _vector_store is None:
        from services.vector_store import VectorStore
        _vector_store = VectorStore()
    return _vector_store

def _get_bm25_index():
    global _bm25_index
    if _bm25_index is None:
        from services.bm25_index import BM25Index
        _bm25_index = BM25Index()
    return _bm25_index


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("rfp_engine.log")
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RFP AI Engine",
    description="Processes RFP documents from Azure Blob Storage",
    version="1.0.0"
)

# Register sub-routers
app.include_router(parsing_router)
app.include_router(compliance_router)
app.include_router(proposal_router)
app.include_router(evaluate_rfp_router)


job_store: Dict[str, dict] = {}

class RfpJob(BaseModel):
    jobId: str
    blobUrl: str
    filename: str

class JobResponse(BaseModel):
    status: str
    job_id: str
    message: Optional[str] = None

async def process_rfp_background(job: RfpJob):
    try:
        logger.info(f"[JOB START] {job.jobId} | File: {job.filename}")
        job_store[job.jobId]["status"] = "processing"
        job_store[job.jobId]["updated_at"] = datetime.utcnow().isoformat()

        # ── Step 1: Parse PDF using hybrid parser ──
        logger.info(f"[STEP 1] Running Hybrid Docling + PDFPlumber Extraction...")
        parsed_markdown = await parse_azure_blob_hybrid(job.blobUrl)
        logger.info(f"[STEP 1 DONE] Extracted {len(parsed_markdown)} characters of structural layout.")

        # ── Step 1.5: Hierarchical Parent-Child Chunking ──
        logger.info(f"[STEP 1.5] Slicing layout into hierarchical context trees...")
        parent_chunks, child_chunks = process_markdown_pipeline(parsed_markdown)
        logger.info(f"[STEP 1.5 DONE] Generated {len(parent_chunks)} parent sections, {len(child_chunks)} child chunks.")

        # ── Step 2: Upsert chunks into Qdrant + BM25 ──
        logger.info(f"[STEP 2] Embedding and indexing {len(child_chunks)} chunks...")
        collection_name = f"rfp_{job.jobId[:8]}"
        vector_db_docs = prepare_for_vector_db(child_chunks)

        try:
            vector_store = _get_vector_store()
            vector_store.add_documents(collection_name, vector_db_docs)
            logger.info(f"[STEP 2a] Qdrant upsert complete → collection '{collection_name}'")
        except Exception as ve:
            logger.warning(f"[STEP 2a] Qdrant upsert failed (non-fatal): {ve}")

        try:
            bm25 = _get_bm25_index()
            bm25.index_documents(vector_db_docs)
            logger.info(f"[STEP 2b] BM25 index built with {len(vector_db_docs)} documents")
        except Exception as be:
            logger.warning(f"[STEP 2b] BM25 indexing failed (non-fatal): {be}")

        # ── Step 3: Execute LangGraph Multi-Agent Swarm ──
        logger.info(f"[STEP 3] Launching LangGraph swarm workflow...")
        job_store[job.jobId]["status"] = "running_agents"
        job_store[job.jobId]["updated_at"] = datetime.utcnow().isoformat()

        from agents.workflow import proposal_swarm_graph

        # Convert Chunk objects to dicts for the agent state
        sections_for_agents = [
            {"id": c.id, "heading_path": c.section_path, "content": c.text}
            for c in parent_chunks
        ]

        initial_state = {
            "rfp_text": parsed_markdown,
            "sections": sections_for_agents,
            "plan": {},
            "drafts": {},
            "reviews": [],
            "approved": False,
            "status": "initialized",
        }

        final_state = proposal_swarm_graph.invoke(initial_state)

        result = {
            "parent_sections_count": len(parent_chunks),
            "collection_name": collection_name,
            "drafts_generated": len(final_state.get("drafts", {})),
            "approved": final_state.get("approved", False),
            "reviews": final_state.get("reviews", []),
            "status": final_state.get("status", "completed"),
        }
        logger.info(
            f"[STEP 3 DONE] Swarm complete. "
            f"Drafts: {result['drafts_generated']}, Approved: {result['approved']}"
        )

        # ── Step 4: Mark job as completed ──
        job_store[job.jobId].update({
            "status": "completed",
            "result": result,
            "updated_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat()
        })
        logger.info(f"[JOB DONE] {job.jobId} — full pipeline executed.")

    except Exception as e:
        logger.error(f"[JOB FAILED] {job.jobId} - Error: {str(e)}")
        job_store[job.jobId].update({
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat()
        })

@app.get("/")
async def root():
    return {
        "service": "RFP AI Engine",
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/process-rfp", response_model=JobResponse)
async def process_rfp(job: RfpJob, background_tasks: BackgroundTasks):
    try:
        logger.info(f"[RECEIVED JOB] ID: {job.jobId} | File: {job.filename}")

        job_store[job.jobId] = {
            "job_id": job.jobId,
            "filename": job.filename,
            "blob_url": job.blobUrl,
            "status": "queued",
            "result": None,
            "error": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "completed_at": None
        }

        background_tasks.add_task(process_rfp_background, job)

        return JobResponse(
            status="accepted",
            job_id=job.jobId,
            message=f"Job queued. Poll /job-status/{job.jobId} for updates."
        )

    except Exception as e:
        logger.error(f"[ERROR] Failed to queue job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job_store[job_id]


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_jobs": len([j for j in job_store.values() if j["status"] in ["queued", "processing"]]),
        "total_jobs": len(job_store),
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)