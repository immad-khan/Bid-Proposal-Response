# File: Ingestion Pipeline — Parser & Chunking Services

This document details the document parsing and chunking services in the AI engine.

---

## 📄 1. Layout-Aware Parser (`ai_engine/services/parser_service.py`)

This service implements a hybrid ingestion pipeline that extracts structured text from PDF documents using two libraries:
1. **Docling (from IBM):** Handles layout analysis and exports structured markdown representation of headings, bullet lists, and paragraphs.
2. **PDFPlumber:** Extracts tables with high numerical precision.

```python
import os
from io import BytesIO
from azure.storage.blob.aio import BlobClient as AsyncBlobClient
from docling.document_converter import DocumentConverter
import pdfplumber

converter = DocumentConverter()
```

### Core Functions

#### A. `extract_high_precision_tables(file_bytes)`
Extracts raw grid tables page-by-page.
```python
def extract_high_precision_tables(file_bytes: BytesIO) -> str:
    table_data = []
    with pdfplumber.open(file_bytes) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for table in tables:
                if table:
                    table_data.append(f"--- High-Precision Table (Page {page_num}) ---")
                    for row in table:
                        clean_row = [str(cell).strip() if cell else "" for cell in row]
                        table_data.append(" | ".join(clean_row))
    return "\n".join(table_data)
```
- **Accuracy:** Extracts tabular data to prevent LLM hallucinations when parsing financial budgets or compliance indices.
- **Output:** Returns pipe-delimited text blocks with page headers.

---

#### B. `parse_azure_blob_hybrid(blob_url)`
An asynchronous orchestrator that downloads the target RFP PDF file from Azure Blob Storage and executes the hybrid parsing pipeline:
1. **Async Download:** Initializes `AsyncBlobClient` from the provided URL, downloads the file stream asynchronously, and stores the buffer in memory.
2. **Layout Extraction (Docling):** Converts the binary stream into a Docling object and exports it as markdown, preserving hierarchical layout information.
3. **Tabular Extraction (PDFPlumber):** Extracts tables from the same byte stream using `extract_high_precision_tables`.
4. **Context Fusion:** Appends the high-precision tables to the bottom of the layout markdown under a `## APPENDIX: HIGH-PRECISION EXTRACTIONS` heading.

---

## ✂️ 2. Chunking Service (`ai_engine/services/chunking_service.py`)

This service segments parsed markdown documents into chunks for vector search indexers. It uses a **Parent-Child Chunking** strategy with **Contextual Prepend** metadata (Anthropic-style Contextual Retrieval).

### Data Structures: `Chunk`
```python
@dataclass
class Chunk:
    id: str                         # Unique hash of text content + heading path
    text: str                       # Extracted plain text content
    chunk_type: str                 # 'parent' or 'child'
    section_path: List[str]         # Path, e.g. ['Technical Requirements', 'Security']
    page_start: int                 # Starting page index
    page_end: int                   # Ending page index
    token_count: int                # Token count approximation
    parent_id: str = None           # References parent ID (if it is a child chunk)
    contextual_prepend: str = ""    # Pre-calculated context context block
```

---

### Core Functions

#### A. `split_markdown_by_headers(markdown_text)`
Parses markdown text into sections using heading level markers (`#`, `##`, `###`).
- **Page Trackers:** Detects comment page tags (e.g. `<!-- page=5 -->`) to track page boundaries for each section.
- **Returns:** A list of sections, each containing the heading path, text content, start page, and end page.

---

#### B. `create_parent_child_chunks(sections, max_child_tokens, overlap_tokens)`
Implements the parent-child chunking logic:
1. **Parent Chunks:** The entire section represents a parent chunk. This provides complete context for retrieval.
2. **Child Chunks:** If the parent section exceeds `max_child_tokens`, it splits the content into smaller child chunks.
3. **Overlap:** Includes previous sentence endings at chunk boundaries to prevent loss of context.
4. **Small Sections:** If a section fits within the token limit, a single child chunk is created that mirrors the parent.

---

#### C. `add_contextual_prepend(chunks, llm_client)`
Implements Anthropic's **Contextual Retrieval** pattern. It generates a brief context summary for each chunk to improve retrieval accuracy.
- **LLM Assisted:** If an LLM client is available, it prompts the model to summarize the chunk's position and topic within the document.
- **Fallback Rule-Based:** If no LLM client is provided, it falls back to a template:
  `[Section: Header1 > Header2 | Pages X-Y]`

---

#### D. `prepare_for_vector_db(child_chunks)`
Formats the processed child chunks into documents ready for indexing in Qdrant:
- **`text_for_embedding`**: The combination of `contextual_prepend` and the chunk's text.
- **`original_text`**: The raw text, stored in the vector database payload but not embedded.
- **Metadata**: Stores the parent ID link, page indexes, token count, and section path.
