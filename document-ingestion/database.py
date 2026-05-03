"""
Database initialization module.
This separates SQLAlchemy from app initialization to avoid circular imports.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
