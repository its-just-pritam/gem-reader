from flask import Blueprint, request, jsonify
from models import ChatHistory
from database import db
from sqlalchemy import text
from limiter import limiter

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat/history", methods=["GET"])
@limiter.limit("2 per 5 seconds")
def get_chat_history():
    """List all previous chats for a specific URL and user."""
    url = request.args.get("url")
    user_id = request.args.get("user_id", "0") # Default to 0 as used in generate route

    if not url:
        return jsonify({"error": "URL parameter is required"}), 400

    try:
        query = """
            SELECT id, query, response, created_at
            FROM chat_history
            WHERE url = :url AND user_id = :user_id
            ORDER BY created_at ASC
        """
        params = {
            'url': url,
            'user_id': str(user_id)
        }

        history = db.session.execute(text(query), params).fetchall()
        
        return jsonify({
            "success": True,
            "history": [
                {
                    "id": h.id,
                    "query": h.query,
                    "response": h.response,
                    "created_at": h.created_at.isoformat()
                } for h in history
            ]
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve chat history: {str(e)}"}), 500