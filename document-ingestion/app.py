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

app = Flask(__name__)
app.config.update(FLASK_CONFIG)
db.init_app(app)

# Import models after db is initialized
from models import Embedding

# Import routes
from routes.health import health_bp
from routes.ingestion import ingestion_bp
from routes.search import search_bp

if __name__ == "__main__":

    # Create database tables
    with app.app_context():
        db.session.execute(text('CREATE EXTENSION IF NOT EXISTS vector;'))
        db.session.commit()
        db.create_all()
        # Create vector index
        db.session.execute(text('CREATE INDEX IF NOT EXISTS embedding_vector_idx ON embeddings USING ivfflat (embedding vector_cosine_ops);'))
        db.session.commit()

    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(ingestion_bp)
    app.register_blueprint(search_bp)

    # Run the Flask app
    app.run(debug=True, host="0.0.0.0", port=5000)
