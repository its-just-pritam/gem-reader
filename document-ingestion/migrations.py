"""
Database migration utilities for manual SQL tasks and table creation.
"""
from sqlalchemy import text
from database import db
from models import Embedding, ChatHistory

def run_migrations():
    """
    Handles database setup: extensions, tables, and custom indexes.
    """
    print("Running database migrations...")
    
    # 1. Ensure vector extension is available (must happen before table creation)
    db.session.execute(text('CREATE EXTENSION IF NOT EXISTS vector;'))
    db.session.commit()

    # 2. Create tables defined in models
    db.create_all()

    # 3. Create indexes
    db.session.execute(text('CREATE INDEX IF NOT EXISTS embedding_vector_idx ON embeddings USING ivfflat (embedding vector_cosine_ops);'))
    db.session.execute(text('CREATE INDEX IF NOT EXISTS embeddings_model_id_idx ON embeddings (model_id);'))
    db.session.execute(text('CREATE INDEX IF NOT EXISTS embeddings_model_name_idx ON embeddings (model_display_name);'))
    db.session.execute(text('CREATE INDEX IF NOT EXISTS embeddings_url_idx ON embeddings (url);'))
    db.session.execute(text('CREATE INDEX IF NOT EXISTS embeddings_user_id_idx ON embeddings (user_id);'))
    
    db.session.commit()
    print("Database migrations applied successfully.")