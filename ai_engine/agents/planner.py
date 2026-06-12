"""
Planner Agent — Analyzes parsed RFP sections and builds a structured
generation plan with requirement-level assignments, retrieved evidence,
and capability gap assessments using LLM analysis.
"""

import logging
from typing import Dict, Any, List

from agents.state import AgentState
from services.compliance_matrix import ComplianceMatrixService

logger = logging.getLogger(__name__)

PLANNING_SYSTEM_PROMPT = """\
You are a Proposal Planning Specialist. You analyze RFP requirements and create
structured response plans. You output valid JSON only."""

PLANNING_PROMPT_TEMPLATE = """\
Analyze the following RFP section and create a detailed response plan.

**Section Path:** {section_path}
**Section Content:**
{section_content}

Create a plan entry as a JSON object with these exact keys:
- "id": a short identifier like "req_0", "req_1", etc. Use "{req_id}" for this one.
- "section": the section heading path
- "requirement_summary": a 1-2 sentence summary of what the RFP requires
- "response_strategy": brief strategy for how to respond (2-3 sentences)
- "evidence_needed": list of 2-3 types of evidence or past work to reference
- "compliance_type": one of "mandatory", "desirable", or "informational"
- "estimated_length": suggested word count for the response (integer)

Respond with ONLY the JSON object, no markdown fences."""


class PlannerAgent:
    """
    Agent responsible for analyzing the parsed RFP sections and building
    an outline of all response requirements (a checklist) with assignments,
    evidence needs, and compliance classifications.
    """

    def __init__(self, llm_client=None, retrieval_service=None):
        self.llm_client = llm_client
        self.retrieval_service = retrieval_service

    def plan(self, state: AgentState) -> Dict[str, Any]:
        """
        Build a structured generation plan from the parsed RFP sections.

        Steps:
            1. Iterate over parsed sections from state.
            2. For each section, query the LLM to classify the requirement
               and suggest a response strategy.
            3. Optionally retrieve similar past proposals for context.
            4. Return the assembled plan checklist.

        Args:
            state: Current LangGraph agent state containing 'sections'.

        Returns:
            Dict with 'plan' and 'status' to merge into agent state.
        """
        logger.info("PlannerAgent: Building RFP response plan.")
        sections = state.get("sections", [])

        if not sections:
            logger.warning("PlannerAgent: No sections found in state.")
            return {
                "plan": {"title": "Empty Plan", "checklist": [], "version": "1.0"},
                "status": "Planning skipped — no sections.",
            }

        requirements_checklist: List[Dict[str, Any]] = []

        for idx, sec in enumerate(sections):
            heading_path = sec.get("heading_path", ["Untitled Section"])
            heading = " > ".join(heading_path)
            content = sec.get("content", "")

            req_id = f"req_{idx}"

            if self.llm_client and content.strip():
                # ── LLM-driven planning ──
                try:
                    prompt = PLANNING_PROMPT_TEMPLATE.format(
                        section_path=heading,
                        section_content=content[:2000],  # cap at 2000 chars
                        req_id=req_id,
                    )
                    plan_entry = self.llm_client.generate_json(
                        prompt=prompt,
                        system_prompt=PLANNING_SYSTEM_PROMPT,
                        max_tokens=512,
                        temperature=0.1,
                    )

                    # Ensure critical fields are present
                    plan_entry.setdefault("id", req_id)
                    plan_entry.setdefault("section", heading)
                    plan_entry.setdefault("assigned_to", "writer")
                    requirements_checklist.append(plan_entry)

                    logger.info(f"PlannerAgent: Planned [{req_id}] — {heading}")
                except Exception as e:
                    logger.error(f"PlannerAgent: LLM planning failed for [{req_id}] — {e}")
                    # Fallback to basic entry
                    requirements_checklist.append(self._basic_plan_entry(req_id, heading, content))
            else:
                # ── Fallback without LLM ──
                requirements_checklist.append(self._basic_plan_entry(req_id, heading, content))

        plan_output = {
            "title": "RFP Response Generation Plan",
            "checklist": requirements_checklist,
            "total_sections": len(requirements_checklist),
            "version": "1.0",
        }

        # ── Step 4: Push to Neo4j Compliance Graph ──
        try:
            neo4j = ComplianceMatrixService()
            for req in requirements_checklist:
                neo4j.create_requirement_node(
                    requirement_id=req["id"],
                    section_path=req["section"],
                    description=req["requirement_summary"],
                    is_mandatory=req.get("compliance_type") == "mandatory"
                )
            neo4j.close()
            logger.info("PlannerAgent: Pushed requirements to Neo4j successfully.")
        except Exception as e:
            logger.warning(f"PlannerAgent: Failed to push to Neo4j - {e}")

        logger.info(f"PlannerAgent: Plan complete — {len(requirements_checklist)} requirements identified.")
        return {"plan": plan_output, "status": "Planning completed."}

    @staticmethod
    def _basic_plan_entry(req_id: str, heading: str, content: str) -> Dict[str, Any]:
        """Create a minimal plan entry when LLM is unavailable."""
        return {
            "id": req_id,
            "section": heading,
            "requirement_summary": content[:300] if content else "Section content not available.",
            "response_strategy": f"Draft a comprehensive response covering {heading}.",
            "evidence_needed": ["past_proposals", "capability_statements"],
            "compliance_type": "mandatory",
            "estimated_length": 500,
            "assigned_to": "writer",
        }
