# DocMind – AI-Powered Document Q&A Assistant

DocMind is an AI-powered application that enables users to upload documents and ask questions about their content using natural language. It uses Retrieval-Augmented Generation (RAG) to retrieve relevant information and generate context-aware answers.

## Key Features

- Supports PDF, DOCX, PPTX, XLSX, CSV and TXT files.
- Ask questions about uploaded documents.
- Generate context-aware answers using document retrieval.
- Display source references for document-based answers.
- Switch between Document Mode and General AI Mode.
- Get AI-generated suggested questions.
- Maintain chat history using SQLite.
- Delete individual conversations or clear chat history.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Frontend | Streamlit |
| Backend | FastAPI |
| Embedding Model | all-MiniLM-L6-v2 |
| Vector Database | ChromaDB |
| Large Language Model API | Groq |
| Chat History Database | SQLite |
| Document Processing | pypdf, python-docx, python-pptx, openpyxl |

## How DocMind Works

DocMind follows a Retrieval-Augmented Generation (RAG) workflow.

1. **Document Upload:** The user uploads a supported document.
2. **Text Extraction:** Text is extracted from the uploaded file.
3. **Text Chunking:** The extracted content is divided into smaller chunks.
4. **Embedding Generation:** Sentence Transformers converts the chunks into vector embeddings.
5. **Vector Storage:** ChromaDB stores the embeddings for semantic retrieval.
6. **Question Processing:** The user's question is converted into a search query.
7. **Context Retrieval:** Relevant document chunks are retrieved.
8. **Answer Generation:** The retrieved context is passed to the Groq language model to generate an answer.
9. **Source Display:** The application displays available source references with the answer.

## Application Modes

### 1. Document Mode
Allows users to ask questions about an uploaded document. Answers are generated using relevant retrieved document content.

### 2. General AI Mode
Allows users to ask general questions without requiring an uploaded document.

## Project Structure

```text
DocMind/
│
├── app.py              # Streamlit frontend
├── main.py             # FastAPI backend and API endpoints
├── ingest.py           # Document text extraction and ingestion
├── retriever.py        # Relevant document retrieval
├── llm.py              # LLM integration and answer generation
├── database.py         # SQLite chat history management
├── evaluate.py         # Evaluation utilities
├── requirements.txt    # Python dependencies
├── .gitignore          # Files excluded from Git
└── README.md           # Project documentation
```

Local folders such as `uploads/` and `chroma_db/`, and the local chat database, are created during application use and are not included in the repository.

## Installation and Setup

### Prerequisites
- Python 3.10 or later
- Git
- A Groq API key

### 1. Clone the repository

```bash
git clone https://github.com/riyaladhania/DocMind.git
cd DocMind
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment (Windows)

```powershell
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root directory:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

Replace the placeholder with your own Groq API key. Never upload the `.env` file or expose your API key publicly.

### 6. Run the backend

Open a terminal in the project directory:

```bash
uvicorn main:app
```

### 7. Run the frontend

Open a second terminal in the same project directory:

```bash
streamlit run app.py
```

The application will open in your browser, usually at:

http://localhost:8501

## Current Limitations

- The application currently supports one active document at a time.
- Scanned PDFs requiring OCR are not supported.
- Embedded images and charts are not interpreted as visual content.

## Future Enhancements

- OCR support for scanned documents.
- Multi-document question answering.
- Improved document management.
- User authentication.
- Cloud deployment.
- Enhanced source referencing and document analysis.

## Project Purpose

DocMind was developed as an academic project to explore Generative AI, Retrieval-Augmented Generation, semantic search, API development and document processing.

## Author

Developed as an academic project.
