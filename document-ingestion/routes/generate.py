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
            if not isinstance(query_text, str) or not query_text.strip():
                continue

            # Generate embedding for the query
            query_embedding = embedding_generator.generate_embeddings([query_text.strip()])
            if not query_embedding or 'predictions' not in query_embedding or not query_embedding['predictions']:
                continue

            query_vector = query_embedding['predictions'][0]
            
            # Unwrap if the embedding is nested in an extra array
            if isinstance(query_vector, list) and len(query_vector) > 0 and isinstance(query_vector[0], (list, tuple)):
                query_vector = query_vector[0]

            # Build search query with model consistency filters
            search_query = """
                SELECT id, text, page_number, keywords, 
                    1 - (embedding <=> CAST(:query_vector AS vector)) AS similarity
                FROM embeddings
                WHERE model_id = :model_id AND model_display_name = :model_name
            """
            params = {
                'query_vector': query_vector,
                'model_id': current_model_id,
                'model_name': current_model_name
            }

            if url_filter:
                search_query += " AND url = :url"
                params['url'] = url_filter

            search_query += " ORDER BY embedding <=> CAST(:query_vector AS vector) LIMIT 5"

            # Perform vector search in DB (cosine similarity)
            search_results = db.session.execute(text(search_query), params).fetchall()
            matches = [{
                "text": row[1],
                "page_number": row[2]
            } for row in search_results]

            prompt = f"""
            You are a helpful professor and expert. Use the following context to answer the user's question. 
            If the answer isn't in the context, say you don't know. Be direct and simple in your response.
            Try to explain your reasoning step by step and ask follow up questions if needed to clarify the user's intent.

            Constraint: 
            Max 200 words in the answer. If the answer is not found in the context, say "I don't know". 
            Do not use any information that is not in the context. If the answer exceeds 200 words, ask the
            user if they want to continue the answer in a follow-up response.

            Format:
            Markdown with headings, subheadings, examples, paragraphs, bullet points, code snippets, and tables as needed.
            Use emojis to make it engaging.

            Note:
            The context may contain information from multiple pages of a PDF. 
            Pay attention to the page numbers and use them to provide accurate references in your answer.

            Context: 
            {matches}

            User Question: 
            {query_text}
            """

            generated_response = model.generate_content(prompt)

            results.append({
                "query": query_text,
                "answer": generated_response.text,
            })

        return jsonify({
            "results": results
        }), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500