"""
Embedding endpoints for PDF processing.

This module contains all endpoints related to generating embeddings:
- /embed - Upload a PDF file
- /embed-only - Send pre-chunked text
- /embed-from-url - Download and process PDF from URL
"""

import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from utils import (
    allowed_file,
    download_pdf_from_url,
    extract_text_with_structure,
    chunk_text_by_structure,
)
from embeddings import PDFEmbeddingGenerator
from config import FLASK_CONFIG
from models import Embedding
from database import db

ingestion_bp = Blueprint("ingestion", __name__)

# Initialize the embedding generator
embedding_generator = PDFEmbeddingGenerator()

@ingestion_bp.route("/ingest/pdf", methods=["POST"])
def embed_from_url():
    """
    API endpoint to download a PDF from a URL and generate embeddings.

    Expected request:
    - Content-Type: application/json
    - JSON body: {"url": "https://example.com/document.pdf"}

    Returns:
    - JSON with chunks and embeddings
    """
    try:
        data = request.get_json()

        if not data or "url" not in data:
            return jsonify({"error": "No URL provided in request"}), 400

        url = data["url"].strip()

        if not url:
            return jsonify({"error": "URL cannot be empty"}), 400

        # Generate a temporary filename
        filename = "temp_" + str(hash(url))[-10:] + ".pdf"
        filepath = os.path.join(FLASK_CONFIG["UPLOAD_FOLDER"], filename)

        # Download the PDF
        download_pdf_from_url(url, filepath)

        # Extract text with structure preservation
        text_elements = extract_text_with_structure(filepath)
        print(f"+++++++Extracted {len(text_elements)} text elements from PDF at URL: {url}")

        if not text_elements:
            os.remove(filepath)
            return jsonify({"error": "No text extracted from PDF"}), 400

        # Chunk the text intelligently
        chunks, keywords, pages = chunk_text_by_structure(text_elements, max_words=800)
        print(f"+++++++Extracted {len(text_elements)} text elements, created {len(chunks)} chunks.")
        print(f"+++++++Pages found: {pages}")

        if not chunks:
            os.remove(filepath)
            return jsonify({"error": "Failed to create chunks"}), 400

        # Generate embeddings
        embeddings = embedding_generator.generate_embeddings(chunks)
        print(f"+++++++Generated {len(embeddings['predictions'])} embeddings for PDF at URL: {url}")

        data = [{
            "model": embeddings['model'],
            "model_id": embeddings['deployedModelId'],
            "model_display_name": embeddings['modelDisplayName'],
            "model_version": embeddings['modelVersionId'],
            "text": chunk, 
            "embedding": embedding[0] if isinstance(embedding, list) and len(embedding) > 0 else embedding,
            "text_length": len(chunk.split()),
            "embedding_length": len(embedding[0]) if isinstance(embedding, list) and len(embedding) > 0 else len(embedding),
            "page_number": page_numbers,
            "keywords": keyword_items,
            "queries": [],
            "tags": []
        } for chunk, page_numbers, keyword_items, embedding in zip(chunks, pages, keywords, embeddings['predictions'])]

        # Save to database
        for item in data:
            chunk_record = Embedding(
                model=item['model'],
                model_id=item['model_id'],
                model_display_name=item['model_display_name'],
                model_version=item['model_version'],
                text=item['text'],
                embedding=item['embedding'],
                text_length=item['text_length'],
                embedding_length=item['embedding_length'],
                page_number=item['page_number'],
                keywords=item['keywords'],
                queries=item['queries'],
                tags=item['tags'],
                url=url,
                user_id=0
            )
            db.session.add(chunk_record)
        db.session.commit()

        # Clean up the temporary file
        os.remove(filepath)

        # Return results
        return (
            jsonify({
                "success": True,
                "url": url,
                "total": len(chunks),
                "data": data
            }), 200
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
