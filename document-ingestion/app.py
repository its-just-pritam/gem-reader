"""
Flask API for generating embeddings from PDF documents.

This API accepts PDF documents, intelligently chunks them while maintaining
structure (headings and paragraphs), and generates embeddings using
GCP's Embedding Gemma model.
"""

import os
from flask import Flask
from config import FLASK_CONFIG
from database import db
from sqlalchemy import text
from migrations import run_migrations

app = Flask(__name__)
app.config.update(FLASK_CONFIG)
db.init_app(app)

# Import routes
from routes.health import health_bp
from routes.ingestion import ingestion_bp
from routes.search import search_bp
from routes.generate import generate_bp

if __name__ == "__main__":

    # Initialize database structure and apply custom migrations
    with app.app_context():
        run_migrations()

    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(ingestion_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(generate_bp)

    # Run the Flask app
    app.run(debug=True, host="0.0.0.0", port=5000)
