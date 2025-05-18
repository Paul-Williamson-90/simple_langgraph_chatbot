import requests

import fitz
from langchain_core.tools import tool


@tool("read_hf_paper_from_url")
def read_hf_paper_from_url(url: str) -> str:
    """Fetches a paper (PDF) from a given URL and extracts its text content.
    This tool should be used with HuggingFace (HF) papers that link to an ArXiv PDF.

    Args:
    url : str
        The URL of the PDF file to fetch and read.
    """
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '').lower()
        if 'application/pdf' not in content_type:
            return f"Error: URL does not point to a PDF file (Content-Type: {content_type})"

        pdf_content = response.content
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")

        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()

        pdf_document.close()
        return text

    except requests.exceptions.RequestException as e:
        return f"Error downloading PDF: {e}"
    except fitz.errors.FitzError as e:
        return f"Error processing PDF: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"