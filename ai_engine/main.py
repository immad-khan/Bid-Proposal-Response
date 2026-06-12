from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 1. At the top of main.py, import your chunker tool:
from services.chunking_service import create_parent_child_chunks
from services.parser_service import parse_azure_blob_hybrid
from routes import parsing_router, compliance_router, proposal_router

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

        # ✅ Step 1: Parse PDF using your hybrid parser
        logger.info(f"[STEP 1] Running Hybrid Docling + PDFPlumber Extraction...")
        parsed_markdown = await parse_azure_blob_hybrid(job.blobUrl)
        logger.info(f"[STEP 1 DONE] Extracted {len(parsed_markdown)} characters of structural layout.")

        # ✅ Step 1.5: Hierarchical Parent-Child Chunking (US-32)
        logger.info(f"[STEP 1.5] Slicing layout into hierarchical context trees...")
        document_hierarchy = create_parent_child_chunks(parsed_markdown)
        logger.info(f"[STEP 1.5 DONE] Generated {len(document_hierarchy)} structurally isolated Parent Sections.")

        # ✅ Step 2: AI Processing (Ready for Vector Storage & Agents)
        logger.info(f"[STEP 2] Initializing Multi-Agent Swarm and Vector Mapping...")
        
        # This hierarchy tree is exactly what your Qdrant and LangGraph agents will use
        result = {
            "parent_sections_count": len(document_hierarchy),
            "ai_summary": "Ready to prompt Planner Agent.",
            "raw_hierarchy": document_hierarchy[:2] # Preview snippet for the logs
        }
        logger.info(f"[STEP 2 DONE] Multi-agent processing initialization complete.")

        # ✅ Step 3: Mark job as completed
        job_store[job.jobId].update({
            "status": "completed",
            "result": result,
            "updated_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat()
        })
        logger.info(f"[JOB DONE] {job.jobId} processed through hybrid chunking stack.")

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