from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import logging
from datetime import datetime

# ✅ Import your parser
from parser_rfp import parse_azure_blob_hybrid  # rename file to parser_rfp.py

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
        logger.info(f"[STEP 1] Parsing PDF: {job.filename}")
        parsed_content = await parse_azure_blob_hybrid(job.blobUrl)
        logger.info(f"[STEP 1 DONE] Parsed {len(parsed_content)} characters")

        # ✅ Step 2: AI Processing (placeholder for now)
        logger.info(f"[STEP 2] Running AI analysis...")
        # TODO: Send parsed_content to OpenAI/Azure OpenAI
        # ai_result = await send_to_openai(parsed_content)
        result = {
            "parsed_content": parsed_content,
            "ai_summary": "TODO: Connect to OpenAI",
            "char_count": len(parsed_content)
        }
        logger.info(f"[STEP 2 DONE] AI analysis complete")

        # ✅ Step 3: Mark job as completed
        job_store[job.jobId].update({
            "status": "completed",
            "result": result,
            "updated_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat()
        })

        logger.info(f"[JOB DONE] {job.jobId} completed successfully")

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