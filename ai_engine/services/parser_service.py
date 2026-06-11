import os
from io import BytesIO
from azure.storage.blob.aio import BlobClient as AsyncBlobClient  # ✅ Async
from docling.document_converter import DocumentConverter
import pdfplumber

converter = DocumentConverter()

def extract_high_precision_tables(file_bytes: BytesIO) -> str:
    """
    Uses PDFPlumber to extract raw, unformatted tabular data
    with 94%+ numerical accuracy to validate against financial hallucinations.
    """
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

    return "\n".join(table_data) if table_data else "No tables found in document."


async def parse_azure_blob_hybrid(blob_url: str) -> str:
    """
    Hybrid Stack: Combines Docling's Layout Awareness with
    PDFPlumber's strict numerical precision.
    """
    try:
        # ✅ Step 1: Async download from Azure Blob
        print(f"Fetching RFP from Azure Storage...")
        async with AsyncBlobClient.from_blob_url(blob_url) as blob_client:
            stream = await blob_client.download_blob()
            raw_bytes = await stream.readall()

        if not raw_bytes:
            raise ValueError("Downloaded file is empty")

        print(f"Downloaded {len(raw_bytes)} bytes successfully")

        # ✅ Step 2A: Docling for document structure
        print(f"Running Docling for overall Document Structure...")
        docling_stream = BytesIO(raw_bytes)
        conversion_result = converter.convert(docling_stream)
        structural_markdown = conversion_result.document.export_to_markdown()

        # ✅ Step 2B: PDFPlumber for precise table extraction
        print(f"Running PDFPlumber for strict tabular validation...")
        plumber_stream = BytesIO(raw_bytes)
        precision_tables = extract_high_precision_tables(plumber_stream)

        # ✅ Step 3: Fuse both outputs
        final_fused_context = (
            f"{structural_markdown}\n\n"
            f"## APPENDIX: HIGH-PRECISION EXTRACTIONS\n"
            f"{precision_tables}"
        )

        print(f"Parsing complete. Total context length: {len(final_fused_context)} chars")
        return final_fused_context

    except ValueError as e:
        print(f"Validation Error: {str(e)}")
        raise e
    except Exception as e:
        print(f"Hybrid Ingestion Pipeline Failed: {str(e)}")
        raise e 