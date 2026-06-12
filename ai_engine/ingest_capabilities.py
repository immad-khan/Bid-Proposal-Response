import os
import sys
import logging
import pandas as pd
import uuid

# Ensure ai_engine is in path to import services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.vector_store import VectorStore
from services.bm25_index import BM25Index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ingest_capabilities():
    excel_path = "../Problem#1_Sample_Datasets (TEKROWE).xlsx"
    collection_name = "capability_library"
    
    logger.info(f"Loading capability library from {excel_path}")
    
    try:
        # The sheet name is likely 'Capability Library' as per problem statement
        # If it's different, we can just read the first sheet or find it.
        xls = pd.ExcelFile(excel_path)
        sheet_name = None
        for name in xls.sheet_names:
            if "capability" in name.lower():
                sheet_name = name
                break
                
        if not sheet_name:
            sheet_name = xls.sheet_names[0] # Fallback to first sheet
            logger.warning(f"Could not find sheet with 'capability' in name. Using '{sheet_name}'")
            
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        logger.info(f"Loaded {len(df)} records from {sheet_name}.")
        
        # We need to convert each row into a document chunk
        documents = []
        for index, row in df.iterrows():
            # Convert row to dictionary, dropping NaNs
            row_dict = {str(k): str(v) for k, v in row.items() if pd.notna(v)}
            
            # Create a rich text representation for embedding
            text_parts = []
            for k, v in row_dict.items():
                text_parts.append(f"{k.replace('_', ' ').title()}: {v}")
                
            full_text = "\n".join(text_parts)
            
            doc_id = str(uuid.uuid4())
            documents.append({
                "id": doc_id,
                "text_for_embedding": full_text,
                "original_text": full_text,
                "metadata": {
                    "source": "capability_library",
                    "row_index": index
                }
            })
            
        # 1. Upsert to Qdrant Vector Store
        vector_store = VectorStore()
        logger.info(f"Upserting {len(documents)} documents to Qdrant collection '{collection_name}'...")
        vector_store.add_documents(collection_name, documents)
        logger.info("Successfully ingested capability library to Qdrant.")
        
        # Note: Since BM25 is currently in-memory, we can't persist it here directly
        # However, the backend should be configured to load from Qdrant/Excel on startup
        # if hybrid search over capabilities is required.
        
    except Exception as e:
        logger.error(f"Failed to ingest capabilities: {e}")

if __name__ == "__main__":
    ingest_capabilities()
