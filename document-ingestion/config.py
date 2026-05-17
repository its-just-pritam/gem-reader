"""
Global configuration for the Flask app and related modules.
"""

import os

DB_NAME = os.getenv("DB_NAME", "gem_reader")
DB_USER = os.getenv("DB_USER", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")


# Flask-specific configs
FLASK_CONFIG = {
    "MAX_CONTENT_LENGTH": 50 * 1024 * 1024,  # 50MB max file size
    "UPLOAD_FOLDER": "/tmp",  # Or os.path.join(os.getcwd(), "uploads") for relative path
    "DEBUG": True,
    "HOST": "0.0.0.0",
    "PORT": 5000,
    "SQLALCHEMY_DATABASE_URI": os.getenv("DATABASE_URL", f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"),
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    "CHUNK_SIZE": 2000,  # Max tokens per chunk,
    "BATCH_SIZE": 10,  # Number of chunks to process in a single batch for embedding generation
}

# GCP/Embeddings-specific configs
GCP_CONFIG = {
    "PROJECT_NAME": "gem-reader",
    "PROJECT_ID": os.getenv("GCP_PROJECT_ID", "gem-reader"),  # Use env vars for secrets
    "LOCATION": os.getenv("GCP_LOCATION", "asia-south1"),
    "ENDPOINT_ID": os.getenv("GCP_ENDPOINT_ID", "mg-endpoint-25701b72-8e96-47d7-a08c-c9856ada9301"),  # Replace "YOUR_ENDPOINT_ID"
    "DEDICATED_DOMAIN": "mg-endpoint-25701b72-8e96-47d7-a08c-c9856ada9301.asia-south1-788531557962.prediction.vertexai.goog",
    "MODEL_DISPLAY_NAME": "embeddinggemma-300m-1777627519039",
    "MODEL_ID": "937648123004583936",
    "DB_INSTANCE": "gem-reader:asia-south1:gem-reader-vector-metadata-store",
    "LLM_MODEL_NAME": "gemini-2.5-flash",
}

# You can add more sections as needed (e.g., database, API keys)