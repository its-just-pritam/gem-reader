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
from prompts.summary_prompts import QUERY_ENHANCEMENT_PROMPT_TEMPLATE
from models import ChatHistory
from config import GCP_CONFIG

vertexai.init(project=GCP_CONFIG["PROJECT_NAME"], location=GCP_CONFIG["LOCATION"])

generate_bp = Blueprint("generate", __name__)

# Initialize the embedding generator
embedding_generator = PDFEmbeddingGenerator()

# Initialize the LLM
llm = GenerativeModel(GCP_CONFIG["LLM_MODEL_NAME"])

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

        # Use db.session.query because 'query' is shadowed by a column name in the model
        last_chat = (
            db.session.query(ChatHistory)
            .filter_by(url=url_filter, user_id="0")
            .order_by(ChatHistory.created_at.desc())
            .first()
        )

        if last_chat:
            enhanced_queries = [
                llm.generate_content(QUERY_ENHANCEMENT_PROMPT_TEMPLATE.format(
                    previous_query=last_chat.query,
                    previous_response=last_chat.response,
                    new_query=query
                )).text
            for query in queries]
        else:
            enhanced_queries = queries


        results = []

        for query_text, enhanced_query_text in zip(queries, enhanced_queries):
            chat_entry = ChatHistory(
                query=query_text,
                enhanced_query=enhanced_query_text,
                response="NA",  # Will be updated after generating response
                embedding_model_id=current_model_id,
                embedding_model_display_name=current_model_name,
                url=url_filter,
                user_id=0
            )
            db.session.add(chat_entry)

            search_results = fetch_search_results(enhanced_query_text, current_model_id, current_model_name, url_filter)

            # Format the context matches into a structured string for better RAG performance
            context_text = "\n\n".join([f"Source (Page {row[2]}): {row[1]}" for row in search_results])

            prompt = RAG_PROMPT_TEMPLATE.format(matches=context_text, query_text=enhanced_query_text, response_size=300)

            generated_response = llm.generate_content(prompt)

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