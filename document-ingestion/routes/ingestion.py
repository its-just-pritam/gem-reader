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
from vertexai.generative_models import GenerativeModel
import vertexai
from config import GCP_CONFIG
from prompts.summary_prompts import SUMMARY_PROMPT_TEMPLATE

vertexai.init(project=GCP_CONFIG["PROJECT_NAME"], location=GCP_CONFIG["LOCATION"])

ingestion_bp = Blueprint("ingestion", __name__)

# Initialize the embedding generator
embedding_generator = PDFEmbeddingGenerator()

# Initialize the LLM
llm = GenerativeModel(GCP_CONFIG["LLM_MODEL_NAME"])

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
        train = request.args.get('train')

        if not data or "url" not in data:
            return jsonify({"error": "No URL provided in request"}), 400

        url = data["url"].strip()

        if not url:
            return jsonify({"error": "URL cannot be empty"}), 400

        print(f"+++++++Received request to ingest PDF from URL: {url} with train={train}")

        # Check for skip cache parameter (e.g., /ingest/pdf?train=true)
        skip_cache = True if (train and train.lower() == "true") else False

        # Get current model info for cache check
        current_model_id = embedding_generator.get_embedding_model_id()
        current_model_name = embedding_generator.get_embedding_model_display_name()

        # Return cached embeddings if the URL and model match
        existing_records = Embedding.query.filter_by(
            url=url,
            model_id=current_model_id,
            model_display_name=current_model_name
        ).all() if not skip_cache else []

        if existing_records:
            print(f"+++++++Found {len(existing_records)} existing records for URL: {url}")
            data = [
                {
                    "model": record.model,
                    "model_id": record.model_id,
                    "model_display_name": record.model_display_name,
                    "model_version": record.model_version,
                    "text": record.text,
                    "embedding": [float(x) for x in record.embedding] if record.embedding is not None else None,
                    "text_length": record.text_length,
                    "embedding_length": record.embedding_length,
                    "page_number": record.page_number,
                    "keywords": record.keywords,
                    "queries": record.queries,
                    "tags": record.tags,
                }
                for record in existing_records
            ]
            return jsonify({"success": True, "url": url, "total": len(data), "data": data}), 200

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
        chunks, keywords, pages = chunk_text_by_structure(text_elements, max_words=FLASK_CONFIG["CHUNK_SIZE"])
        print(f"+++++++Extracted {len(text_elements)} text elements, created {len(chunks)} chunks.")
        print(f"+++++++Pages found: {pages}")

        if not chunks:
            os.remove(filepath)
            return jsonify({"error": "Failed to create chunks"}), 400

        prompt = SUMMARY_PROMPT_TEMPLATE.format(context=text_elements, response_size=FLASK_CONFIG["CHUNK_SIZE"])
        summary = llm.generate_content(prompt)
        if(summary and summary.text and len(summary.text.strip()) > FLASK_CONFIG["CHUNK_SIZE"]):
            prompt = SUMMARY_PROMPT_TEMPLATE.format(context=text_elements, response_size=(FLASK_CONFIG["CHUNK_SIZE"]-50))
            summary = llm.generate_content(prompt)
        print(f"+++++++Generated summary for PDF at URL: {url}")

        chunks.append(summary.text)  # Add the summary as an additional chunk
        keywords.append([])  # No keywords for the summary chunk
        pages.append(0)  # Page number 0 for the summary chunk

        # Generate embeddings
        embeddings = embedding_generator.generate_embeddings(chunks)
        
        if not embeddings or 'predictions' not in embeddings:
            return jsonify({"error": "Failed to generate embeddings: Model endpoint returned no data"}), 500
            
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
        print(f"+++++++ValueError: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"+++++++ValueError: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
