"""
Chunking Service – Hierarchical Parent-Child Chunking with Metadata
Supports contextual prepend, page/section tracking, and output formats for vector storage.
"""

import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
import hashlib

# Optional: if you use a small LLM for contextual prepend (e.g., via litellm or Groq)
# from services.llm_client import generate_context

@dataclass
class Chunk:
    """Represents a single chunk (parent or child)"""
    id: str                     # unique chunk ID (hash of content + path)
    text: str                   # the actual text content
    chunk_type: str             # 'parent' or 'child'
    section_path: List[str]     # e.g. ['Technical Requirements', 'Security', 'ISO 27001']
    page_start: int
    page_end: int
    token_count: int
    parent_id: str = None       # for child chunks, link to parent chunk ID
    contextual_prepend: str = ""   # added before embedding (Anthropic style)
    metadata: Dict[str, Any] = None

    def to_dict(self):
        return asdict(self)

    def get_text_for_embedding(self) -> str:
        """Return the text that should be embedded (contextual prepend + original)"""
        if self.contextual_prepend:
            return f"{self.contextual_prepend}\n\n{self.text}"
        return self.text


def split_markdown_by_headers(markdown_text: str) -> List[Dict[str, Any]]:
    """
    Splits markdown into sections based on headings (#, ##, ###).
    Returns list of {'heading_path': list, 'content': str, 'start_page': int, 'end_page': int}
    Assumes page markers like `<!-- page=5 -->` are present in markdown (from parser).
    """
    sections = []
    lines = markdown_text.split('\n')
    current_heading_path = []
    current_content = []
    current_page_start = 1
    current_page_end = 1
    
    # Regex to capture page markers (customise based on your parser output)
    page_marker_re = re.compile(r'<!--\s*page=(\d+)\s*-->')
    
    for line in lines:
        # Detect page markers
        page_match = page_marker_re.search(line)
        if page_match:
            current_page_end = int(page_match.group(1))
            continue
        
        # Detect markdown headings (e.g., '# Title', '## Subtitle')
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
        if heading_match:
            # Save previous section
            if current_content:
                sections.append({
                    'heading_path': current_heading_path.copy(),
                    'content': '\n'.join(current_content).strip(),
                    'start_page': current_page_start,
                    'end_page': current_page_end
                })
                current_content = []
                current_page_start = current_page_end
            
            # Update heading path
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            # Truncate path to level
            current_heading_path = current_heading_path[:level-1] + [title]
        else:
            current_content.append(line)
    
    # Add last section
    if current_content:
        sections.append({
            'heading_path': current_heading_path,
            'content': '\n'.join(current_content).strip(),
            'start_page': current_page_start,
            'end_page': current_page_end
        })
    
    return sections


def create_parent_child_chunks(
    sections: List[Dict[str, Any]], 
    max_child_tokens: int = 400,
    overlap_tokens: int = 50
) -> Tuple[List[Chunk], List[Chunk]]:
    """
    Creates parent chunks (full sections) and child chunks (sub‑splits).
    Returns (parent_chunks, child_chunks).
    Uses simple token approximation (words/0.75) – replace with tiktoken if needed.
    """
    parent_chunks = []
    child_chunks = []
    
    for sec in sections:
        heading_path = sec['heading_path']
        content = sec['content']
        start_page = sec['start_page']
        end_page = sec['end_page']
        
        # Approximate token count (English: ~0.75 tokens per word)
        approx_tokens = len(content.split()) // 0.75
        
        # Parent chunk = full section
        parent_id = hashlib.md5(f"{heading_path}_{start_page}".encode()).hexdigest()[:12]
        parent = Chunk(
            id=parent_id,
            text=content,
            chunk_type='parent',
            section_path=heading_path,
            page_start=start_page,
            page_end=end_page,
            token_count=int(approx_tokens),
            metadata={'full_section': True}
        )
        parent_chunks.append(parent)
        
        # Split content into child chunks if needed
        if approx_tokens > max_child_tokens:
            # Simple split by sentences or paragraphs; for production, use a proper splitter
            paragraphs = content.split('\n\n')
            current_text = ""
            current_tokens = 0
            child_index = 0
            
            for para in paragraphs:
                para_tokens = len(para.split()) // 0.75
                if current_tokens + para_tokens > max_child_tokens and current_text:
                    # create child chunk
                    child_id = f"{parent_id}_chunk_{child_index}"
                    child = Chunk(
                        id=child_id,
                        text=current_text.strip(),
                        chunk_type='child',
                        section_path=heading_path,
                        page_start=start_page,
                        page_end=end_page,
                        token_count=current_tokens,
                        parent_id=parent_id
                    )
                    child_chunks.append(child)
                    child_index += 1
                    # overlap: keep last part of previous chunk (optional)
                    current_text = current_text.split('.')[-2] + '. ' if overlap_tokens > 0 else ""
                    current_tokens = len(current_text.split()) // 0.75
                
                current_text += para + "\n\n"
                current_tokens += para_tokens
            
            # final child
            if current_text:
                child_id = f"{parent_id}_chunk_{child_index}"
                child = Chunk(
                    id=child_id,
                    text=current_text.strip(),
                    chunk_type='child',
                    section_path=heading_path,
                    page_start=start_page,
                    page_end=end_page,
                    token_count=current_tokens,
                    parent_id=parent_id
                )
                child_chunks.append(child)
        else:
            # section is small – create one child that mirrors parent
            child = Chunk(
                id=f"{parent_id}_chunk_0",
                text=content,
                chunk_type='child',
                section_path=heading_path,
                page_start=start_page,
                page_end=end_page,
                token_count=int(approx_tokens),
                parent_id=parent_id
            )
            child_chunks.append(child)
    
    return parent_chunks, child_chunks


def add_contextual_prepend(chunks: List[Chunk], llm_client=None) -> List[Chunk]:
    """
    For each chunk, generate a short context using a small LLM and prepend it.
    This implements Anthropic's "Contextual Retrieval".
    If no LLM client provided, creates a simple rule‑based context.
    """
    for chunk in chunks:
        if llm_client:
            prompt = f"""Given the following chunk from a document, write a very short (1‑2 sentences) context that explains where it appears in the document. Include document title (if known), section path, and the main topic.

Section path: {' > '.join(chunk.section_path)}

Chunk text:
{chunk.text[:500]}...

Context:"""
            try:
                context = llm_client.generate(prompt, max_tokens=60, temperature=0)
                chunk.contextual_prepend = context.strip()
            except:
                # fallback
                chunk.contextual_prepend = f"[Section: {' > '.join(chunk.section_path)}]"
        else:
            # simple fallback without LLM
            chunk.contextual_prepend = f"[Section: {' > '.join(chunk.section_path)} | Pages {chunk.page_start}-{chunk.page_end}]"
    return chunks


def prepare_for_vector_db(child_chunks: List[Chunk]) -> List[Dict[str, Any]]:
    """
    Convert child chunks into documents ready for insertion into ChromaDB.
    Each item includes:
        - id (chunk.id)
        - embedding_text (chunk.get_text_for_embedding())
        - metadata (section_path, page numbers, parent_id, etc.)
    """
    documents = []
    for chunk in child_chunks:
        doc = {
            "id": chunk.id,
            "text_for_embedding": chunk.get_text_for_embedding(),
            "original_text": chunk.text,   # stored but not embedded
            "metadata": {
                "chunk_type": chunk.chunk_type,
                "section_path": " > ".join(chunk.section_path),
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "parent_id": chunk.parent_id,
                "token_count": chunk.token_count,
                "contextual_prepend": chunk.contextual_prepend
            }
        }
        documents.append(doc)
    return documents


# ========== Example usage if run standalone ==========
if __name__ == "__main__":
    # Sample markdown with page markers (simulated)
    sample_md = """<!-- page=1 -->
# Executive Summary
This RFP seeks a vendor to provide cloud services.

<!-- page=2 -->
## Technical Requirements
The system must have 99.9% uptime.
- Scalability
- Security

### Sub-requirement: ISO 27001
Vendor must be certified.

<!-- page=3 -->
## Budget
Total cost not to exceed $500k.
"""
    sections = split_markdown_by_headers(sample_md)
    parent_chunks, child_chunks = create_parent_child_chunks(sections, max_child_tokens=200)
    child_chunks = add_contextual_prepend(child_chunks, llm_client=None)  # using fallback
    
    docs_for_vector_db = prepare_for_vector_db(child_chunks)
    
    print(f"Created {len(child_chunks)} child chunks")
    for doc in docs_for_vector_db[:2]:
        print(f"\nID: {doc['id']}")
        print(f"Embedding text (first 200 chars): {doc['text_for_embedding'][:200]}...")
        print(f"Metadata: {doc['metadata']}")