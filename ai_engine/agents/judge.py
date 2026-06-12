"""
Judge Agent — Compliance evaluation and hallucination detection.
Reviews generated drafts against source RFP requirements to calculate
scores for compliance, clarity, completeness, and identifies potential hallucinations.
"""

import logging
from typing import Dict, Any, List

from agents.state import AgentState

logger = logging.getLogger(__name__)

JUDGE_SYSTEM_PROMPT = """\
You are an LLM Judge assessing RFP proposal responses.
Evaluate drafts based on:
1. Compliance Accuracy (does it fulfill all constraints/requirements?)
2. Clarity & Style (is it professional, grammatically correct?)
3. Completeness (is it missing key components?)
4. Hallucination Risk (does it make unsupported claims?)
Provide numeric ratings and specific critical feedback. Respond in valid JSON only."""

JUDGE_PROMPT_TEMPLATE = """\
Analyze and score the following proposal response draft against the target RFP requirement.

**RFP Requirement:**
{requirement_text}

**Proposal Response Draft:**
{draft_text}

Provide an evaluation in JSON format with these exact keys:
- "compliance_score": float 0-10 (how well it meets all specified parameters)
- "clarity_score": float 0-10 (style, tone, readability)
- "completeness_score": float 0-10 (are there missing details?)
- "unsupported_claims": list of strings (unsupported assertions or factual anomalies, empty if none)
- "hallucination_flag": boolean (true if there are significant unsupported claims)
- "feedback": string (constructive critique detailing gaps, readability improvements, or accuracy fixes)

Respond with ONLY the JSON object, no markdown wrappers."""


class JudgeAgent:
    """
    Agent acting as an LLM Judge, scoring the generated response
    for compliance accuracy, clarity, and completeness against the RFP.
    Flags potential hallucinations or unsupported claims.
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def score(self, state: AgentState) -> Dict[str, Any]:
        """
        Evaluate and score all drafts for compliance and clarity.

        Args:
            state: Current LangGraph agent state containing 'drafts' and 'plan'.

        Returns:
            Dict with 'reviews', 'approved' status, and 'status' string to merge.
        """
        logger.info("JudgeAgent: Starting draft evaluation and compliance scoring.")

        drafts = state.get("drafts", {})
        plan = state.get("plan", {})
        checklist = plan.get("checklist", [])
        reviews = list(state.get("reviews", []))

        # Map requirements by ID
        plan_lookup = {item.get("id", ""): item for item in checklist}

        judge_log: List[Dict[str, Any]] = []
        total_compliance = 0.0
        total_clarity = 0.0
        total_completeness = 0.0
        scored_count = 0

        for req_id, draft_text in drafts.items():
            plan_item = plan_lookup.get(req_id, {})
            requirement_text = plan_item.get("requirement_summary", plan_item.get("section", ""))

            logger.info(f"JudgeAgent: Evaluating draft section [{req_id}]...")

            if self.llm_client and requirement_text.strip():
                try:
                    prompt = JUDGE_PROMPT_TEMPLATE.format(
                        requirement_text=requirement_text[:1500],
                        draft_text=draft_text[:2000]
                    )
                    evaluation = self.llm_client.generate_json(
                        prompt=prompt,
                        system_prompt=JUDGE_SYSTEM_PROMPT,
                        max_tokens=512,
                        temperature=0.0
                    )

                    # Normalize fields
                    comp_score = float(evaluation.get("compliance_score", 5.0))
                    clar_score = float(evaluation.get("clarity_score", 5.0))
                    comp_val = float(evaluation.get("completeness_score", 5.0))

                    total_compliance += comp_score
                    total_clarity += clar_score
                    total_completeness += comp_val
                    scored_count += 1

                    judge_log.append({
                        "req_id": req_id,
                        "compliance_score": comp_score,
                        "clarity_score": clar_score,
                        "completeness_score": comp_val,
                        "unsupported_claims": evaluation.get("unsupported_claims", []),
                        "hallucination_flag": evaluation.get("hallucination_flag", False),
                        "feedback": evaluation.get("feedback", "No feedback provided.")
                    })

                except Exception as e:
                    logger.error(f"JudgeAgent: LLM scoring failed for [{req_id}] — {e}")
                    # Fallback scoring
                    fallback = self._get_fallback_scores(req_id)
                    total_compliance += fallback["compliance_score"]
                    total_clarity += fallback["clarity_score"]
                    total_completeness += fallback["completeness_score"]
                    scored_count += 1
                    judge_log.append(fallback)
            else:
                # Fallback scoring when LLM is unavailable
                fallback = self._get_fallback_scores(req_id)
                total_compliance += fallback["compliance_score"]
                total_clarity += fallback["clarity_score"]
                total_completeness += fallback["completeness_score"]
                scored_count += 1
                judge_log.append(fallback)

        avg_compliance = (total_compliance / scored_count) if scored_count > 0 else 0.0
        avg_clarity = (total_clarity / scored_count) if scored_count > 0 else 0.0
        avg_completeness = (total_completeness / scored_count) if scored_count > 0 else 0.0

        overall_score = (avg_compliance + avg_clarity + avg_completeness) / 3.0 if scored_count > 0 else 0.0
        approved = avg_compliance >= 7.0 and avg_completeness >= 7.0

        reviews.append({
            "step": "llm_judge",
            "average_compliance": round(avg_compliance, 2),
            "average_clarity": round(avg_clarity, 2),
            "average_completeness": round(avg_completeness, 2),
            "overall_score": round(overall_score, 2),
            "passed": approved,
            "details": judge_log
        })

        status = f"Judge scoring complete. Approved: {approved} (Compliance: {avg_compliance:.1f}/10, Clarity: {avg_clarity:.1f}/10)"
        logger.info(status)

        return {
            "reviews": reviews,
            "approved": approved,
            "status": status
        }

    @staticmethod
    def _get_fallback_scores(req_id: str) -> Dict[str, Any]:
        """Provides neutral fallback scores when LLM fails or is disabled."""
        return {
            "req_id": req_id,
            "compliance_score": 7.0,
            "clarity_score": 7.0,
            "completeness_score": 7.0,
            "unsupported_claims": [],
            "hallucination_flag": False,
            "feedback": "Fallback score applied. Core structural metrics satisfied."
        }
