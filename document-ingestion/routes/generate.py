"""
Search endpoints for vector similarity search.

This module contains endpoints for searching embeddings:
- /search - Perform vector search with queries
"""

from flask import Blueprint, request, jsonify
from embeddings import PDFEmbeddingGenerator
from vertexai.generative_models import GenerativeModel
from sqlalchemy import text
from database import db
import vertexai
import re
from .search import fetch_search_results
from prompts.rag_prompts import RAG_PROMPT_TEMPLATE
from models import ChatHistory

vertexai.init(project="gem-reader", location="asia-south1")

generate_bp = Blueprint("generate", __name__)

# Initialize the embedding generator
embedding_generator = PDFEmbeddingGenerator()

# Initialize the LLM
model = GenerativeModel("gemini-2.5-flash")

@generate_bp.route("/generate", methods=["POST"])
def vector_search():
    """
    API endpoint to perform vector search.

    Expected request:
    - Content-Type: application/json
    - JSON body: {"queries": ["query1", "query2", ...]}

    Returns:
    - JSON with search results for each query
    """
    try:
        data = request.get_json()

        if not data or "queries" not in data:
            return jsonify({"error": "No queries provided in request"}), 400

        queries = data["queries"]
        if not isinstance(queries, list) or not queries:
            return jsonify({"error": "Queries must be a non-empty list"}), 400

        # Get current model info and optional URL filter
        current_model_id = embedding_generator.get_embedding_model_id()
        current_model_name = embedding_generator.get_embedding_model_display_name()
        url_filter = data.get("url")

        results = []

        for query_text in queries:
            chat_entry = ChatHistory(
                query=query_text,
                response="NA",  # Will be updated after generating response
                embedding_model_id=current_model_id,
                embedding_model_display_name=current_model_name,
                url=url_filter,
                user_id=0
            )
            db.session.add(chat_entry)

            search_results = fetch_search_results(query_text, current_model_id, current_model_name, url_filter)

            matches = [{
                "text": row[1],
                "page_number": row[2]
            } for row in search_results]

            prompt = RAG_PROMPT_TEMPLATE.format(matches=matches, query_text=query_text, response_size=300)

            generated_response = model.generate_content(prompt)

            results.append({
                "query": query_text,
                "answer": generated_response.text,
            })

            # Update the chat entry with the generated response
            chat_entry.response = generated_response.text
            db.session.commit()

        return jsonify({
            "results": results
        }), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500