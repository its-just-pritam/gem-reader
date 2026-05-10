<p align="center">
  <img src="icon.png" alt="Gem Reader Logo" width="128">
</p>

# Gem Reader 📖

Gem Reader (chrome-extension) is a powerful, AI-driven document assistant that transforms how you interact with PDF files in your Chrome browser. By leveraging Retrieval-Augmented Generation (RAG), Gem Reader detects when you're reading a PDF and provides a dedicated chat interface to help you summarize content, extract insights, and ask complex questions—all with accurate page references.

## 🌟 Key Features

- **Smart PDF Detection**: Automatically identifies PDF content in the browser and offers to initiate analysis.
- **AI-Powered Chat Assistant**: Uses Google Gemini to provide intelligent, context-aware answers.
- **Citations & References**: Pay close attention to page numbers; the assistant references specific pages to ensure accuracy.
- **Persistent History**: Saves your conversations locally and in the cloud so you can pick up where you left off.
- **Markdown Support**: High-quality rendering of headers, lists, and code snippets in the chat interface.
- **Vector Search**: Combines Cosine Similarity and Euclidean Distance to find the most relevant context for your questions.

## 🏗️ Architecture

### Chrome Extension (Frontend)
- **Manifest V3**: Built using the latest extension standards.
- **Content Scripts**: Injects a custom, responsive UI into the PDF viewer.
- **Background Worker**: Handles cross-origin requests and communicates with the backend API.
- **Storage Integration**: Uses `chrome.storage.local` to track document ingestion status.

### Ingestion & RAG Service (Backend)
- **Flask API**: A robust Python service handling document processing and search.
- **Vector Database**: PostgreSQL with the `pgvector` extension for efficient semantic search.
- **Vertex AI Integration**: 
  - **Embedding Gemma**: Used for high-dimensional text vectorization.
  - **Gemini Flash 2.0**: Powers the generative reasoning and response generation.

## 🚀 Getting Started

### Backend Setup
1. **Database**: Ensure you have a PostgreSQL instance with the `vector` extension installed.

2. **Configuration**: Update `document-ingestion/config.py` with your credentials:
   ```python
   SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost:5432/gem_reader"
   GCP_PROJECT_ID = "your-project-id"
   ```
3. **Enter the backend directory and set up a virtual environment**
    ```bash
   cd document-ingestion
   python3 -m venv venv
   source venv/bin/activate
   ```
4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Run Application**:
   ```bash
   python app.py
   ```
   *The server will initialize database migrations and start on port 5000.*

### Extension Installation
1. Open Chrome and go to `chrome://extensions/`.
2. Toggle **Developer mode** (top right).
3. Click **Load unpacked** and select the `chrome-extension/` folder in this repository.

## 🛠️ Project Structure

```text
├── chrome-extension/      # Manifest, background scripts, and UI logic
│   ├── icons/             # Extension iconography
│   ├── content.js         # UI injection and message handling
│   └── background.js      # API orchestration
├── document-ingestion/    # Python Backend
│   ├── routes/            # API endpoints (ingestion, search, chat, generate)
│   ├── prompts/           # RAG prompt templates
│   ├── models.py          # Database schema (Embeddings, ChatHistory)
│   ├── utils.py           # PDF processing and chunking logic
│   └── app.py             # Flask entry point
└── readme.md              # Project documentation
```

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.