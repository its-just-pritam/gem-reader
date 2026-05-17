"""
Utility functions for PDF processing and text chunking.
"""

import re
from typing import List, Dict
import PyPDF2
import requests
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from config import FLASK_CONFIG

# Download required NLTK data (averaged_perceptron_tagger and punkt)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')


ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename: str) -> bool:
    """Check if the uploaded file is a PDF."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def sanitize_text(text: str) -> str:
    """
    Detects and fixes common PDF encoding artifacts.
    
    - Removes null bytes (\x00)
    - Strips CID glyph mappings like /1/2/3/
    - Normalizes whitespace
    """
    if not text:
        return ""
        
    # Remove null bytes which break many text processors
    text = text.replace('\x00', '')
    
    # Remove CID/glyph indices patterns like /1/2/3/4 which are not human readable
    text = re.sub(r'(/[0-9]+)+', ' ', text)
    
    # Normalize multiple whitespaces and newlines into single spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def extract_keywords(text: str) -> List[str]:
    """
    Extract important nouns (keywords) from text.

    Args:
        text: Text to extract keywords from

    Returns:
        List of unique nouns found in the text
    """
    try:
        # Tokenize and POS tag
        tokens = word_tokenize(text.lower())
        pos_tags = pos_tag(tokens)

        # Extract nouns (NN=singular, NNS=plural, NNP=proper singular, NNPS=proper plural)
        nouns = [word for word, pos in pos_tags if pos in ['NN', 'NNS', 'NNP', 'NNPS']]

        # Return unique nouns while preserving order
        seen = set()
        unique_nouns = []
        for noun in nouns:
            if noun not in seen and len(noun) > 2:  # Filter out very short words
                seen.add(noun)
                unique_nouns.append(noun)

        return unique_nouns[:20]  # Return top 20 keywords
    except Exception:
        return []


def download_pdf_from_url(url: str, output_path: str) -> bool:
    """
    Download a PDF file from a URL.

    Args:
        url: URL to the PDF file
        output_path: Path where to save the downloaded PDF

    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"+++++++Attempting to download PDF from URL: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        response = requests.get(url, headers=headers, timeout=120, stream=True)
        response.raise_for_status()

        # Check if content is PDF
        content_type = response.headers.get("content-type", "").lower()
        if "pdf" not in content_type:
            raise ValueError(
                f"URL does not point to a PDF file. Content-Type: {content_type}"
            )

        # Write to file
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return True

    except requests.RequestException as e:
        raise ValueError(f"Failed to download PDF from URL: {e}")
    except Exception as e:
        raise ValueError(f"Error downloading PDF: {e}")


def count_words(text: str) -> int:
    """Count the number of words in a text."""
    return len(text.split())


def extract_text_with_structure(pdf_path: str) -> List[Dict[str, str]]:
    """
    Extract text from PDF while preserving structure (headings, paragraphs).

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of dictionaries with 'type' (heading/paragraph), 'text', and 'page_num'
    """
    text_elements = []

    try:
        with open(pdf_path, "rb") as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()

                if not text:
                    continue

                # Split by double newlines to identify paragraphs
                paragraphs = text.split("\n\n")

                for para in paragraphs:
                    para = para.strip()
                    
                    # Sanitize the text before processing
                    para = sanitize_text(para)
                    if not para or len(para) < 2:
                        continue

                    # Simple heuristic: short lines with few words might be headings
                    lines = para.split("\n")
                    if len(lines) == 1 and count_words(para) < 15:
                        # Likely a heading
                        text_elements.append({"type": "heading", "text": para, "page_num": page_num + 1})
                    else:
                        # Treat as paragraph
                        text_elements.append({"type": "paragraph", "text": para, "page_num": page_num + 1})

    except FileNotFoundError:
        raise ValueError(f"PDF file '{pdf_path}' not found.")
    except Exception as e:
        raise ValueError(f"Error extracting text from PDF: {e}")

    return text_elements


def chunk_text_by_structure(
    text_elements: List[Dict[str, str]]) -> tuple:
    """
    Chunk text with 10% overlap between consecutive chunks using character count.

    Args:
        text_elements: List of text elements with type, content, and page_num

    Returns:
        Tuple of (chunks, keywords, pages) where:
        - chunks: List of text chunks with 10% overlap
        - keywords: List of keyword lists (one per chunk with important nouns)
        - pages: List of page numbers corresponding to each chunk
    """
    max_chars = FLASK_CONFIG["CHUNK_SIZE"]
    
    # Collect all text with their page numbers and track page start indices
    all_text = ""
    char_page_map = []
    page_starts = {}  # page_num -> start index in all_text

    for element in text_elements:
        text = element["text"].strip()
        if text:
            page_num = element["page_num"]
            if page_num not in page_starts:
                page_starts[page_num] = len(all_text)
            
            text_to_add = text + " "
            all_text += text_to_add
            char_page_map.extend([page_num] * len(text_to_add))

    if not all_text:
        return [], [], []

    # Sliding window with 10% overlap based on characters
    overlap_chars = int(max_chars * 0.1)
    step = max_chars - overlap_chars
    chunks = []
    keywords = []
    pages = []
    chunk_start_pages = set()  # Track pages that have chunks starting on them

    for i in range(0, len(all_text), step):
        chunk_text = all_text[i : i + max_chars].strip()
        if chunk_text:
            chunk_page = char_page_map[i]
            chunk_keywords = extract_keywords(chunk_text)

            chunks.append(chunk_text)
            keywords.append(chunk_keywords)
            pages.append(chunk_page)
            chunk_start_pages.add(chunk_page)

    # Ensure at least one chunk per page
    for page_num, start_idx in page_starts.items():
        if page_num not in chunk_start_pages:
            chunk_text = all_text[start_idx : start_idx + max_chars].strip()
            if chunk_text:
                chunk_keywords = extract_keywords(chunk_text)
                chunks.append(chunk_text)
                keywords.append(chunk_keywords)
                pages.append(page_num)

    # Log results for debugging
    if chunks:
        print(f"+++++++First chunk sample: {chunks[0][:100]}...")
        chunk_sizes = [len(chunk) for chunk in chunks]
        print(f"+++++++Final chunk sizes (in characters): {chunk_sizes}")

    return chunks, keywords, pages
