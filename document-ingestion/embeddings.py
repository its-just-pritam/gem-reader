"""
Generate embeddings from PDF documents using GCP's Embedding Gemma model.

This script extracts text from PDF documents and generates embeddings
using Google Cloud's VertexAI Embedding Gemma model.
"""

import os
from typing import List, Dict, Any
import PyPDF2
from google.cloud import aiplatform
from google.oauth2 import service_account
from config import GCP_CONFIG
import json
import requests
import google.auth
import google.auth.transport.requests

class PDFEmbeddingGenerator:
    """Generate embeddings for PDF documents using Embedding Gemma."""

    def __init__(self):
        # Initialize the PDF Embedding Generator.
        try:
            self.embeddings_url = f"https://{GCP_CONFIG['DEDICATED_DOMAIN']}/v1/projects/{GCP_CONFIG['PROJECT_ID']}/locations/{GCP_CONFIG['LOCATION']}/endpoints/{GCP_CONFIG['ENDPOINT_ID']}:predict"
            print(f"+++++++ Initialized Gemma Endpoint: {GCP_CONFIG['ENDPOINT_ID']}")
        except Exception as e:
            print(f"------- Error initializing embedding model: {e}")
            

    def generate_embeddings(self, text_chunks: List[str]) -> Dict[str, Any]:

        # Automatically get credentials (equivalent to gcloud auth print-access-token)
        # This looks for credentials set by 'gcloud auth application-default login'
        credentials, project = google.auth.default()
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)

        batch_size = 50  # Process in batches to avoid 413 errors and payload limits
        final_result = {}
        all_predictions = []

        try:
            for i in range(0, len(text_chunks), batch_size):
                batch = text_chunks[i:i+batch_size]
                print(f"+++++++ Generating embeddings for batch {i//batch_size + 1} ({len(batch)} chunks)...")
                
                response = requests.post(
                    self.embeddings_url,
                    headers={
                        "Authorization": f"Bearer {credentials.token}",
                        "Content-Type": "application/json"
                    }, 
                    json={
                        "instances": [{"inputs": chunk} for chunk in batch]
                    }
                )
                
                # Raise an exception if the request was unsuccessful
                response.raise_for_status()
                res_json = response.json()
                
                if not final_result:
                    final_result = res_json
                    all_predictions = res_json.get('predictions', [])
                else:
                    all_predictions.extend(res_json.get('predictions', []))
            
            final_result['predictions'] = all_predictions
            return final_result

        except requests.exceptions.HTTPError as err:
            print(f"------- HTTP error occurred: {err}")
            if 'response' in locals() and response.text:
                print(f"------- Response Body: {response.text}")
            raise
        except Exception as e:
            print(f"------- An unexpected error occurred\n{e}")
            raise

    def get_embedding_model_display_name(self) -> str:
        """Return the display name for the embedding model."""
        return GCP_CONFIG['MODEL_DISPLAY_NAME']

    def get_embedding_model_id(self) -> str:
        """Return the ID for the embedding model."""
        return GCP_CONFIG['MODEL_ID']
        