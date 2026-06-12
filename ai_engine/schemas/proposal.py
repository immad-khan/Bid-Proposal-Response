"""
Proposal Schemas — Request and response models for generation tasks.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ProposalGenerationRequest(BaseModel):
    projectId: str = Field(..., description="The unique database ID of the proposal project")
    rfpText: str = Field(..., description="Parsed raw RFP text to process")


class ProposalGenerationResponse(BaseModel):
    status: str
    approved: bool
    overall_score: float
    sections_drafted: int
    draft_previews: Dict[str, str]
    compliance_issues_count: int
