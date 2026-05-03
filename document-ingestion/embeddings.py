"""
Generate embeddings from PDF documents using GCP's Embedding Gemma model.

This script extracts text from PDF documents and generates embeddings
using Google Cloud's VertexAI Embedding Gemma model.
"""

import os
from typing import List, Dict
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
            

    def generate_embeddings(self, text_chunks: List[str]) -> List[List[float]]:

        # Automatically get credentials (equivalent to gcloud auth print-access-token)
        # This looks for credentials set by 'gcloud auth application-default login'
        credentials, project = google.auth.default()
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)

        try:
            print(f"+++++++ Generating embeddings for {len(text_chunks)} chunks...")
            response = requests.post(
                self.embeddings_url,
                headers={
                    "Authorization": f"Bearer {credentials.token}",
                    "Content-Type": "application/json"
                }, 
                json={
                    "instances": [{"inputs": chunk} for chunk in text_chunks]
                }
            )
            
            # Raise an exception if the request was unsuccessful (e.g., 400, 404, 500)
            response.raise_for_status()
            
            print(f"+++++++ Received response from Gemma endpoint with status code: {response.status_code}")
            result = response.json()
            return result

        except requests.exceptions.HTTPError as err:
            print(f"------- HTTP error occurred: {err}")
            if response.text:
                print(f"------- Response Body: {response.text}")
        except Exception as e:
            print(f"------- An unexpected error occurred\n{e}")
        