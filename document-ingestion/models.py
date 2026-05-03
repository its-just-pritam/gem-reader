"""
Database models for the Flask app.
"""

from database import db
from sqlalchemy.dialects.postgresql import JSON
from pgvector.sqlalchemy import Vector

class Embedding(db.Model):
    __tablename__ = 'embeddings'

    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(255))
    model_id = db.Column(db.String(255))
    model_display_name = db.Column(db.String(255))
    model_version = db.Column(db.String(255))
    text = db.Column(db.Text)
    embedding = db.Column(Vector(768))  # Assuming 768 dimensions for Gemma embeddings
    text_length = db.Column(db.Integer)
    embedding_length = db.Column(db.Integer)
    page_number = db.Column(db.Integer)
    keywords = db.Column(JSON)  # List of keywords
    queries = db.Column(JSON)   # List of queries
    tags = db.Column(JSON)      # List of tags
    url = db.Column(db.String(2048))  # URL of the source PDF
    user_id = db.Column(db.String(255))  # Optional: to associate with a user
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f'<Embedding {self.id}>'