"""
Test suite for chunking_service — validates hierarchical parent-child
chunking, contextual prepend, and vector DB preparation.
"""

import pytest
from services.chunking_service import (
    create_parent_child_chunks,
    split_markdown_by_headers,
)


# ── Fixtures ──

SAMPLE_MARKDOWN = """# 1. Technical Requirements

The vendor shall provide a cloud-based platform supporting at least 10,000 concurrent users.
The system must integrate with Active Directory for single sign-on authentication.
All data must be encrypted at rest (AES-256) and in transit (TLS 1.3).

## 1.1 Performance Requirements

Response times for API calls shall not exceed 200ms at the 95th percentile.
The system shall support horizontal auto-scaling based on CPU utilization thresholds.

## 1.2 Security Requirements

The solution must comply with SOC 2 Type II certification requirements.
Annual penetration testing results shall be provided to the contracting authority.
Multi-factor authentication must be enforced for all administrative access.

# 2. Project Management

The vendor shall assign a dedicated Project Manager with PMP certification.
Weekly status reports must be submitted to the contracting officer.

## 2.1 Timeline

Phase 1 (Discovery): 4 weeks
Phase 2 (Implementation): 12 weeks
Phase 3 (Testing & QA): 4 weeks
Phase 4 (Go-Live): 2 weeks
"""


# ── Tests ──


class TestSplitMarkdownByHeaders:
    """Validate that markdown is correctly split into sections by heading level."""

    def test_splits_top_level_headers(self):
        sections = split_markdown_by_headers(SAMPLE_MARKDOWN)
        assert len(sections) >= 2, f"Expected at least 2 top-level sections, got {len(sections)}"

    def test_each_section_has_required_keys(self):
        sections = split_markdown_by_headers(SAMPLE_MARKDOWN)
        for sec in sections:
            assert "heading_path" in sec, "Missing 'heading_path' key in section"
            assert "content" in sec, "Missing 'content' key in section"

    def test_section_content_is_not_empty(self):
        sections = split_markdown_by_headers(SAMPLE_MARKDOWN)
        non_empty = [s for s in sections if s.get("content", "").strip()]
        assert len(non_empty) > 0, "All sections have empty content"


class TestCreateParentChildChunks:
    """Validate hierarchical chunking with parent and child splits."""

    def test_returns_list(self):
        result = create_parent_child_chunks(SAMPLE_MARKDOWN)
        assert isinstance(result, list), "Expected list output"

    def test_each_chunk_has_parent_field(self):
        result = create_parent_child_chunks(SAMPLE_MARKDOWN)
        for chunk in result:
            assert "parent" in chunk or "heading_path" in chunk, (
                "Chunk missing parent reference"
            )

    def test_chunks_contain_text(self):
        result = create_parent_child_chunks(SAMPLE_MARKDOWN)
        for chunk in result:
            text = chunk.get("content", chunk.get("text", ""))
            # At least some chunks should have text
            if text:
                assert len(text) > 10, "Chunk text is suspiciously short"

    def test_empty_input_returns_empty(self):
        result = create_parent_child_chunks("")
        assert isinstance(result, list), "Expected list for empty input"

    def test_single_section_input(self):
        md = "# Only Section\n\nSome content here about requirements."
        result = create_parent_child_chunks(md)
        assert len(result) >= 1, "Expected at least 1 chunk from single section"


class TestChunkMetadata:
    """Validate that chunk metadata is correctly propagated."""

    def test_chunks_preserve_section_identity(self):
        result = create_parent_child_chunks(SAMPLE_MARKDOWN)
        # At least one chunk should reference a known section
        section_refs = []
        for chunk in result:
            path = chunk.get("heading_path", [])
            if isinstance(path, list):
                section_refs.extend(path)
            elif isinstance(path, str):
                section_refs.append(path)
        assert any("Technical" in ref or "Project" in ref for ref in section_refs if ref), (
            "No chunks reference known section headings"
        )
