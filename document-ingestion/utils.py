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
        response = requests.get(url, timeout=30, stream=True)
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
                    if not para:
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
    text_elements: List[Dict[str, str]], max_words: int = 300
) -> tuple:
    """
    Chunk text with 20% overlap between consecutive chunks, ensuring at least one chunk per page.

    Args:
        text_elements: List of text elements with type, content, and page_num
        max_words: Maximum words per chunk (default 300)

    Returns:
        Tuple of (chunks, keywords, pages) where:
        - chunks: List of text chunks with 20% overlap and at least one per page
        - keywords: List of keyword lists (one per chunk with important nouns)
        - pages: List of page numbers corresponding to each chunk
    """
    # Collect all words with their page numbers and track page start indices
    all_words = []
    page_starts = {}  # page_num -> start index in all_words
    current_index = 0

    for element in text_elements:
        text = element["text"].strip()
        if text:
            words = text.split()
            page_num = element["page_num"]
            if page_num not in page_starts:
                page_starts[page_num] = current_index
            all_words.extend([(word, page_num) for word in words])
            current_index += len(words)

    if not all_words:
        return [], [], []

    # Sliding window with 20% overlap
    overlap_words = int(max_words * 0.1)
    step = max_words - overlap_words
    chunks = []
    keywords = []
    pages = []
    chunk_start_pages = set()  # Track pages that have chunks starting on them

    for i in range(0, len(all_words), step):
        chunk_words_with_pages = all_words[i : i + max_words]
        if chunk_words_with_pages:
            chunk_text = " ".join(word for word, _ in chunk_words_with_pages).strip()
            chunk_page = chunk_words_with_pages[0][1]  # Page of first word
            chunk_keywords = extract_keywords(chunk_text)

            chunks.append(chunk_text)
            keywords.append(chunk_keywords)
            pages.append(chunk_page)
            chunk_start_pages.add(chunk_page)

    # Ensure at least one chunk per page
    for page_num, start_idx in page_starts.items():
        if page_num not in chunk_start_pages:
            # Add a chunk starting from this page
            chunk_words_with_pages = all_words[start_idx : start_idx + max_words]
            if chunk_words_with_pages:
                chunk_text = " ".join(word for word, _ in chunk_words_with_pages).strip()
                chunk_keywords = extract_keywords(chunk_text)

                chunks.append(chunk_text)
                keywords.append(chunk_keywords)
                pages.append(page_num)

    chunks = [chunk.replace('\x00', '') for chunk in chunks]

    return chunks, keywords, pages
