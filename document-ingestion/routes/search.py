"""
Search endpoints for vector similarity search.

This module contains endpoints for searching embeddings:
- /search - Perform vector search with queries
"""

from flask import Blueprint, request, jsonify
from embeddings import PDFEmbeddingGenerator
from sqlalchemy import text
from database import db
from limiter import limiter

search_bp = Blueprint("search", __name__)

# Initialize the embedding generator
embedding_generator = PDFEmbeddingGenerator()

@search_bp.route("/search", methods=["POST"])
@limiter.limit("2 per 5 seconds")
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
            search_results = fetch_search_results(query_text, current_model_id, current_model_name, url_filter)

            matches = [{
                "id": row[0],
                "text": row[1],
                "page_number": row[2],
                "keywords": row[3],
                "similarity": float(row[4])
            } for row in search_results]

            results.append({
                "query": query_text,
                "matches": matches,
                "total": len(matches)
            })

        return jsonify({
            "results": results
        }), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


def fetch_search_results(query_text, current_model_id, current_model_name, url_filter):
    if not isinstance(query_text, str) or not query_text.strip():
        return []

    # Generate embedding for the query
    query_embedding = embedding_generator.generate_embeddings([query_text.strip()])
    if not query_embedding or 'predictions' not in query_embedding or not query_embedding['predictions']:
        return []

    query_vector = query_embedding['predictions'][0]
    
    # Unwrap if the embedding is nested in an extra array
    if isinstance(query_vector, list) and len(query_vector) > 0 and isinstance(query_vector[0], (list, tuple)):
        query_vector = query_vector[0]
    # Handle case where Vertex AI returns a dictionary with 'values'
    elif isinstance(query_vector, dict) and 'values' in query_vector:
        query_vector = query_vector['values']

    # Perform vector search in DB (cosine similarity)
    print(f"+++++++Performing vector search for query: '{query_text}' with model_id: {current_model_id} and model_display_name: {current_model_name}")
    search_query, params = cosine_match_query(query_vector, current_model_id, current_model_name, url_filter)
    search_results = db.session.execute(text(search_query), params).fetchall()

    if(len(search_results) == 0):
        # Perform vector search in DB (euclidean distance)
        print(f"+++++++No results found with cosine similarity, performing euclidean distance search for query: '{query_text}'")
        search_query, params = euclidean_match_query(query_vector, current_model_id, current_model_name, url_filter)
        search_results = db.session.execute(text(search_query), params).fetchall()

    return search_results


def cosine_match_query(query_vector, current_model_id, current_model_name, url_filter):
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

    search_query += " ORDER BY embedding <=> CAST(:query_vector AS vector) LIMIT 10"

    return search_query, params

def euclidean_match_query(query_vector, current_model_id, current_model_name, url_filter):
    # Build search query with model consistency filters
    search_query = """
        SELECT id, text, page_number, keywords, 
            1 - (embedding <-> CAST(:query_vector AS vector)) AS similarity
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

    search_query += " ORDER BY embedding <-> CAST(:query_vector AS vector) LIMIT 10"

    return search_query, params