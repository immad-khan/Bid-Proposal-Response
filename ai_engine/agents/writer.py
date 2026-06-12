"""
Writer Agent — Generates proposal response sections using RAG.
Retrieves relevant evidence chunks from the knowledge base and uses
an LLM to synthesize a professional, citation-backed response for
each requirement in the plan checklist.
"""

import logging
from typing import Dict, Any

from agents.state import AgentState

logger = logging.getLogger(__name__)

WRITER_SYSTEM_PROMPT = """\
You are a Senior Proposal Writer with expertise in government and enterprise RFP responses.
You write clear, professional, and compliant proposal sections.
Always reference source evidence where applicable using inline citations like [Source: Page X] or [Evidence: chunk_id].
Structure your responses with clear headings, bullet points for key capabilities, and a closing compliance statement."""

WRITER_PROMPT_TEMPLATE = """\
Write a proposal response section for the following RFP requirement.

**Requirement Section:** {section_name}
**Requirement Summary:** {requirement_summary}
**Response Strategy:** {response_strategy}
**Target Length:** approximately {estimated_length} words

**Retrieved Evidence / Context:**
{evidence_text}

**Instructions:**
1. Open with a direct compliance statement addressing the requirement.
2. Provide detailed capabilities, experience, and technical approach.
3. Reference the evidence provided using inline citations [Source: ...].
4. Close with a summary of how the response meets the requirement.
5. Use professional proposal language appropriate for enterprise RFPs.
6. Do NOT include any placeholder text like "TODO" or "[insert here]".

Write the response now:"""


class WriterAgent:
    """
    Agent responsible for writing individual proposal response sections.
    Uses retrieval-augmented generation (RAG) to pull supporting evidence
    from the vector store and BM25 index, then synthesizes professional
    proposal text via the LLM.
    """

    def __init__(self, llm_client=None, retrieval_service=None):
        self.llm_client = llm_client
        self.retrieval_service = retrieval_service

    def write(self, state: AgentState) -> Dict[str, Any]:
        """
        Generate draft content for each requirement in the plan checklist.

        Steps:
            1. Read the plan checklist from state.
            2. For each requirement, retrieve relevant evidence chunks.
            3. Construct a detailed prompt with the requirement + evidence.
            4. Call the LLM to generate the response section.
            5. Store each draft keyed by requirement ID.

        Args:
            state: Current LangGraph agent state containing 'plan'.

        Returns:
            Dict with 'drafts' and 'status' to merge into agent state.
        """
        logger.info("WriterAgent: Starting draft generation for RFP requirements.")

        plan = state.get("plan", {})
        checklist = plan.get("checklist", [])

        if not checklist:
            logger.warning("WriterAgent: Empty checklist — nothing to write.")
            return {"drafts": {}, "status": "No requirements to draft."}

        new_drafts: Dict[str, str] = {}

        for item in checklist:
            req_id = item.get("id", "unknown")
            section_name = item.get("section", "Untitled")
            requirement_summary = item.get("requirement_summary", section_name)
            response_strategy = item.get("response_strategy", "Address the requirement comprehensively.")
            estimated_length = item.get("estimated_length", 500)

            logger.info(f"WriterAgent: Drafting [{req_id}] — {section_name}")

            # ── Step 1: Retrieve supporting evidence ──
            evidence_text = self._retrieve_evidence(requirement_summary)

            if self.llm_client:
                # ── Step 2: LLM-powered drafting ──
                try:
                    prompt = WRITER_PROMPT_TEMPLATE.format(
                        section_name=section_name,
                        requirement_summary=requirement_summary,
                        response_strategy=response_strategy,
                        estimated_length=estimated_length,
                        evidence_text=evidence_text,
                    )
                    draft = self.llm_client.generate(
                        prompt=prompt,
                        system_prompt=WRITER_SYSTEM_PROMPT,
                        max_tokens=min(estimated_length * 2, 4096),
                        temperature=0.3,
                    )
                    new_drafts[req_id] = draft
                    logger.info(f"WriterAgent: Draft [{req_id}] generated ({len(draft)} chars).")

                except Exception as e:
                    logger.error(f"WriterAgent: LLM generation failed for [{req_id}] — {e}")
                    new_drafts[req_id] = self._fallback_draft(section_name, requirement_summary)
            else:
                # ── Fallback without LLM ──
                new_drafts[req_id] = self._fallback_draft(section_name, requirement_summary)

        return {"drafts": new_drafts, "status": f"Drafting completed. {len(new_drafts)} sections written."}

    def _retrieve_evidence(self, query: str) -> str:
        """Retrieve top evidence chunks from the retrieval service."""
        if not self.retrieval_service:
            return "(No retrieval service configured — evidence not available.)"

        try:
            results = self.retrieval_service.retrieve(query, top_n=5)
            if not results:
                return "(No matching evidence found in the knowledge base.)"

            evidence_parts = []
            for i, doc in enumerate(results, 1):
                text = doc.get("original_text", doc.get("text", ""))
                section = doc.get("metadata", {}).get("section_path", "Unknown section")
                page = doc.get("metadata", {}).get("page_start", "?")
                evidence_parts.append(
                    f"[Evidence {i} | Section: {section} | Page: {page}]\n{text[:600]}"
                )
            return "\n\n".join(evidence_parts)

        except Exception as e:
            logger.warning(f"WriterAgent: Evidence retrieval failed — {e}")
            return "(Evidence retrieval encountered an error.)"

    @staticmethod
    def _fallback_draft(section_name: str, requirement_summary: str) -> str:
        """Generate a structural placeholder when LLM is not available."""
        return (
            f"### Response: {section_name}\n\n"
            f"**Requirement:** {requirement_summary}\n\n"
            f"We fully acknowledge and comply with the requirements outlined in this section. "
            f"Our solution provides comprehensive coverage including:\n\n"
            f"- Full alignment with the stated technical and operational requirements\n"
            f"- Proven track record with similar implementations\n"
            f"- Dedicated project team with relevant domain expertise\n"
            f"- Scalable architecture meeting all specified performance criteria\n\n"
            f"*[Detailed evidence to be populated when LLM service is available.]*"
        )
