import io
import logging
from pypdf import PdfReader

logger = logging.getLogger("pdf_extractor")

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extracts text from PDF bytes.
    
    Args:
        pdf_bytes: The raw bytes of the PDF.
        
    Returns:
        The extracted plain text.
    """
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        # If extraction fails, return empty or raise
        raise ValueError(f"Failed to parse PDF resume: {e}")
