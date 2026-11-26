
import os
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field

from ingest import ingest_document
from retriever import retrieve
from llm import (
    answer,
    answer_general,
    suggest_question_groups
)


app = FastAPI()

os.makedirs("uploads", exist_ok=True)

# Supported document formats
ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".csv",
    ".txt"
}


# Data received from the frontend
class AskRequest(BaseModel):
    question: str
    history: list = Field(default_factory=list)
    mode: str = "document"


# Upload and process documents
@app.post("/upload")
def upload(file: UploadFile = File(...)):

    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Upload PDF, DOCX, PPTX, XLSX, CSV or TXT."
        )

    path = os.path.join("uploads", filename)

    try:
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        count = ingest_document(path)

        if count == 0:
            raise HTTPException(
                status_code=400,
                detail="No readable text found in this document."
            )

        return {
            "message": f"Successfully processed {filename}: {count} chunks",
            "filename": filename,
            "chunks": count
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Document processing failed: " + str(e)[:300]
        )

    finally:
        file.file.close()


# Ask questions in Document Mode or General AI Mode
@app.post("/ask")
def ask(body: AskRequest):

    if not body.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Please enter a question."
        )

    try:

        # GENERAL AI MODE
        if body.mode == "general":

            text = answer_general(
                body.question,
                body.history
            )

            return {
                "answer": text,
                "sources": [],
                "suggestions": {
                    "document_questions": [],
                    "general_questions": []
                },
                "mode": "general"
            }

        # DOCUMENT MODE
        elif body.mode == "document":

            try:
                chunks = retrieve(body.question)

            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Please upload a document first."
                )

            text = answer(
                body.question,
                chunks,
                body.history
            )

            # Generate two types of suggestions
            try:
                suggestions = suggest_question_groups(
                    body.question,
                    chunks,
                    text
                )

            except Exception as e:
                print("Suggestion generation failed:", e)

                suggestions = {
                    "document_questions": [],
                    "general_questions": []
                }

            return {
                "answer": text,
                "sources": chunks,
                "suggestions": suggestions,
                "mode": "document"
            }

        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid mode. Choose document or general."
            )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail="The language model returned an error: " + str(e)[:300]
        )
