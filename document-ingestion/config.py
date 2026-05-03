"""
Global configuration for the Flask app and related modules.
"""

import os

# Flask-specific configs
FLASK_CONFIG = {
    "MAX_CONTENT_LENGTH": 50 * 1024 * 1024,  # 50MB max file size
    "UPLOAD_FOLDER": "/tmp",  # Or os.path.join(os.getcwd(), "uploads") for relative path
    "DEBUG": True,
    "HOST": "0.0.0.0",
    "PORT": 5000,
    "SQLALCHEMY_DATABASE_URI": os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/gem_reader"),
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
}

# GCP/Embeddings-specific configs
GCP_CONFIG = {
    "PROJECT_ID": os.getenv("GCP_PROJECT_ID", "649289288067"),  # Use env vars for secrets
    "LOCATION": os.getenv("GCP_LOCATION", "asia-south1"),
    "ENDPOINT_ID": os.getenv("GCP_ENDPOINT_ID", "mg-endpoint-25701b72-8e96-47d7-a08c-c9856ada9301"),  # Replace "YOUR_ENDPOINT_ID"
    "DEDICATED_DOMAIN": "mg-endpoint-25701b72-8e96-47d7-a08c-c9856ada9301.asia-south1-788531557962.prediction.vertexai.goog",
    "DB_INSTANCE": "gem-reader-vector-metadata-store",
}

# You can add more sections as needed (e.g., database, API keys)