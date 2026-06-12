"""
Gatekeeper Agent — Compliance verification and guardrail enforcement.
Validates generated drafts against the original RFP requirements using
semantic similarity scoring and LLM-based contradiction detection.
"""

import logging
from typing import Dict, Any, List

from agents.state import AgentState

logger = logging.getLogger(__name__)

GUARDRAIL_SYSTEM_PROMPT = """\
You are a Compliance Reviewer. You verify that proposal drafts correctly address
RFP requirements without contradictions, unsupported claims, or placeholder text.
Respond with valid JSON only."""

GUARDRAIL_PROMPT_TEMPLATE = """\
Review the following proposal draft against its RFP requirement.

**RFP Requirement:**
{requirement_text}

**Proposal Draft:**
{draft_text}

Evaluate and return a JSON object with these exact keys:
- "addresses_requirement": boolean — does the draft directly address the requirement?
- "has_contradictions": boolean — does the draft contradict the requirement?
- "has_placeholders": boolean — does the draft contain TODO, placeholder, or [insert] text?
- "has_unsupported_claims": boolean — does the draft make claims without evidence?
- "compliance_score": float 0-1 — overall compliance rating
- "issues": list of strings — specific issues found (empty list if none)
- "recommendation": string — "pass", "revise", or "reject"

Respond with ONLY the JSON object."""


class GatekeeperAgent:
    """
    Agent responsible for checking generated drafts against guardrails:
    - Placeholder detection (TODO, [insert], etc.)
    - Requirement coverage verification
    - Contradiction detection
    - Unsupported claims flagging
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def verify(self, state: AgentState) -> Dict[str, Any]:
        """
        Run compliance and guardrail checks on all generated drafts.

        Steps:
            1. Read drafts and plan from state.
            2. For each draft, run structural checks (placeholders, length).
            3. If LLM is available, run semantic compliance analysis.
            4. Aggregate results and determine pass/fail.

        Args:
            state: Current LangGraph agent state containing 'drafts' and 'plan'.

        Returns:
            Dict with 'reviews' and 'status' to merge into agent state.
        """
        logger.info("GatekeeperAgent: Running compliance and guardrail checks.")

        drafts = state.get("drafts", {})
        plan = state.get("plan", {})
        checklist = plan.get("checklist", [])
        reviews = list(state.get("reviews", []))

        # Build a lookup from requirement ID to plan details
        plan_lookup = {item.get("id", ""): item for item in checklist}

        gatekeeper_log: List[Dict[str, Any]] = []
        all_passed = True

        for req_id, draft_text in drafts.items():
            plan_item = plan_lookup.get(req_id, {})
            requirement_text = plan_item.get("requirement_summary", plan_item.get("section", ""))

            logger.info(f"GatekeeperAgent: Checking [{req_id}]...")

            # ── Structural checks (always run) ──
            structural_issues = self._structural_checks(draft_text)

            if self.llm_client and requirement_text.strip():
                # ── LLM-based compliance analysis ──
                try:
                    prompt = GUARDRAIL_PROMPT_TEMPLATE.format(
                        requirement_text=requirement_text[:1500],
                        draft_text=draft_text[:2000],
                    )
                    analysis = self.llm_client.generate_json(
                        prompt=prompt,
                        system_prompt=GUARDRAIL_SYSTEM_PROMPT,
                        max_tokens=512,
                        temperature=0.0,
                    )

                    # Merge structural issues into LLM analysis
                    llm_issues = analysis.get("issues", [])
                    all_issues = structural_issues + llm_issues
                    analysis["issues"] = all_issues

                    passed = (
                        analysis.get("recommendation", "reject") == "pass"
                        and not structural_issues
                    )
                    analysis["passed"] = passed

                    gatekeeper_log.append({"req_id": req_id, **analysis})

                    if not passed:
                        all_passed = False

                except Exception as e:
                    logger.error(f"GatekeeperAgent: LLM check failed for [{req_id}] — {e}")
                    passed = len(structural_issues) == 0
                    gatekeeper_log.append(
                        self._structural_only_result(req_id, structural_issues, passed)
                    )
                    if not passed:
                        all_passed = False
            else:
                # ── Structural checks only ──
                passed = len(structural_issues) == 0
                gatekeeper_log.append(
                    self._structural_only_result(req_id, structural_issues, passed)
                )
                if not passed:
                    all_passed = False

        reviews.append({
            "step": "gatekeeper",
            "passed": all_passed,
            "total_checked": len(gatekeeper_log),
            "issues_found": sum(1 for r in gatekeeper_log if not r.get("passed", True)),
            "checks": gatekeeper_log,
        })

        status = (
            "Gatekeeper: All checks passed."
            if all_passed
            else f"Gatekeeper: {sum(1 for r in gatekeeper_log if not r.get('passed'))} sections need revision."
        )
        logger.info(status)

        return {"reviews": reviews, "status": status}

    @staticmethod
    def _structural_checks(text: str) -> List[str]:
        """
        Run rule-based structural checks on draft text.
        Returns a list of issue descriptions (empty if clean).
        """
        issues = []

        # Check for placeholder markers
        placeholder_markers = ["TODO", "FIXME", "[insert", "[placeholder", "TBD", "lorem ipsum"]
        text_lower = text.lower()
        for marker in placeholder_markers:
            if marker.lower() in text_lower:
                issues.append(f"Contains unresolved placeholder: '{marker}'")

        # Check for suspiciously short responses
        word_count = len(text.split())
        if word_count < 50:
            issues.append(f"Response too short ({word_count} words). Minimum 50 expected.")

        # Check for dummy URLs
        if "example.com" in text_lower or "mockstorage" in text_lower:
            issues.append("Contains dummy/example URLs that need to be replaced.")

        return issues

    @staticmethod
    def _structural_only_result(
        req_id: str, issues: List[str], passed: bool
    ) -> Dict[str, Any]:
        """Build a result dict for structural-only checks."""
        return {
            "req_id": req_id,
            "addresses_requirement": True,  # can't verify without LLM
            "has_contradictions": False,
            "has_placeholders": any("placeholder" in i.lower() or "TODO" in i for i in issues),
            "compliance_score": 1.0 if passed else 0.5,
            "issues": issues,
            "recommendation": "pass" if passed else "revise",
            "passed": passed,
        }
