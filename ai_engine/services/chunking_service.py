import re
import uuid

def split_markdown_by_headers(markdown_text: str):
    """
    Splits layout-aware markdown into distinct structural sections (Parent Chunks)
    based on H1, H2, or H3 markers.
    """
    # Regex to catch Markdown headings (e.g., #, ##, ###)
    heading_pattern = r"(^|\n)(#{1,3}\s+.*)"
    
    parts = re.split(heading_pattern, markdown_text)
    
    sections = []
    current_header = "Introduction / Document Start"
    current_content = ""
    
    # Iterate through split parts to re-assemble headers with their respective bodies
    i = 0
    while i < len(parts):
        part = parts[i]
        if not part:
            i += 1
            continue
        
        # If it matches a header tracker
        if re.match(r"^#{1,3}\s+", part.strip()):
            if current_content.strip():
                sections.append({"header": current_header, "content": current_content.strip()})
            current_header = part.strip()
            current_content = ""
        else:
            current_content += part
        i += 1
        
    if current_content.strip():
        sections.append({"header": current_header, "content": current_content.strip()})
        
    return sections


def create_parent_child_chunks(markdown_text: str, child_size: int = 400):
    """
    Processes the document into a strict Parent-Child hierarchy for ChromaDB injection.
    """
    parent_sections = split_markdown_by_headers(markdown_text)
    processed_hierarchy = []
    
    for section in parent_sections:
        parent_id = str(uuid.uuid4())
        full_parent_text = f"{section['header']}\n\n{section['content']}"
        
        # Split the parent text roughly into smaller child token blocks or character windows
        words = full_parent_text.split()
        child_chunks = []
        
        # Simple windowing for hackathon speed (approx 300-400 words per child)
        for i in range(0, len(words), child_size - 100): # 100 word overlap
            child_text = " ".join(words[i:i + child_size])
            if child_text.strip():
                child_chunks.append({
                    "child_id": str(uuid.uuid4()),
                    "text": child_text,
                    "metadata": {
                        "parent_id": parent_id,
                        "parent_header": section['header'],
                        "type": "child"
                    }
                })
        
        processed_hierarchy.append({
            "parent_id": parent_id,
            "parent_text": full_parent_text,
            "header": section['header'],
            "children": child_chunks
        })
        
    return processed_hierarchy