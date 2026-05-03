"""
Search endpoints for vector similarity search.

This module contains endpoints for searching embeddings:
- /search - Perform vector search with queries
"""

from flask import Blueprint, request, jsonify
from embeddings import PDFEmbeddingGenerator
from sqlalchemy import text
from database import db

search_bp = Blueprint("search", __name__)

# Initialize the embedding generator
embedding_generator = PDFEmbeddingGenerator()

@search_bp.route("/search", methods=["POST"])
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

            # Perform vector search in DB (cosine similarity)
            search_results = db.session.execute(text("""
                SELECT id, text, page_number, keywords, 
                    1 - (embedding <=> CAST(:query_vector AS vector)) AS similarity
                FROM embeddings
                ORDER BY embedding <=> CAST(:query_vector AS vector)
                LIMIT 10
            """), {'query_vector': query_vector}).fetchall()
            matches = [{
                "id": row[0],
                "text": row[1],
                "page_number": row[2],
                "keywords": row[3],
                "similarity": float(row[4])
            } for row in search_results]

            results.append({
                "query": query_text,
                "matches": matches
            })

        return jsonify({"results": results}), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500