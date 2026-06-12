"""
Test suite for chunking_service — validates hierarchical parent-child
chunking, contextual prepend, and vector DB preparation.
"""

from services.chunking_service import (
    create_parent_child_chunks,
    split_markdown_by_headers,
    process_markdown_pipeline,
    prepare_for_vector_db,
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

    def test_returns_parent_and_child_lists(self):
        sections = split_markdown_by_headers(SAMPLE_MARKDOWN)
        parents, children = create_parent_child_chunks(sections)
        assert isinstance(parents, list), "Expected list output for parents"
        assert isinstance(children, list), "Expected list output for children"

    def test_each_child_chunk_has_parent_id(self):
        sections = split_markdown_by_headers(SAMPLE_MARKDOWN)
        parents, children = create_parent_child_chunks(sections)
        for chunk in children:
            assert chunk.parent_id is not None, "Child chunk missing parent ID"

    def test_chunks_contain_text(self):
        sections = split_markdown_by_headers(SAMPLE_MARKDOWN)
        parents, children = create_parent_child_chunks(sections)
        for chunk in parents + children:
            assert len(chunk.text) > 0, "Chunk text is empty"

    def test_empty_input_returns_empty(self):
        parents, children = create_parent_child_chunks([])
        assert len(parents) == 0
        assert len(children) == 0


class TestPipelineAndMetadata:
    """Validate full pipeline and prepared document schemas."""

    def test_pipeline_workflow(self):
        parents, children = process_markdown_pipeline(SAMPLE_MARKDOWN)
        assert len(parents) > 0
        assert len(children) > 0

        # Verify contextual prepend works
        for child in children:
            assert child.contextual_prepend != ""
            assert "Section:" in child.contextual_prepend

        # Verify Qdrant document prep
        docs = prepare_for_vector_db(children)
        assert len(docs) == len(children)
        for doc in docs:
            assert "id" in doc
            assert "text_for_embedding" in doc
            assert "original_text" in doc
            assert "metadata" in doc
            assert doc["metadata"]["parent_id"] is not None
            assert "section_path" in doc["metadata"]
