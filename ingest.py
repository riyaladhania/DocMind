
import os
import csv
from pathlib import Path

from pypdf import PdfReader
from docx import Document
from pptx import Presentation
from openpyxl import load_workbook

from sentence_transformers import SentenceTransformer
import chromadb


# Load embedding model once
model = SentenceTransformer("all-MiniLM-L6-v2")


# Open persistent ChromaDB
client = chromadb.PersistentClient(path="chroma_db")


# Split text into overlapping chunks
def chunk_text(text, size=800, overlap=100):

    chunks = []
    start = 0

    while start < len(text):
        piece = text[start:start + size]

        if piece.strip():
            chunks.append(piece)

        start += size - overlap

    return chunks


# Read PDF
def read_pdf(path):

    reader = PdfReader(path)
    units = []

    for page_no, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        if text.strip():
            units.append((text, f"Page {page_no}", page_no))

    return units


# Read Word DOCX
def read_docx(path):

    doc = Document(path)

    parts = []

    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            parts.append(paragraph.text)

    # Also read Word tables
    for table in doc.tables:
        for row in table.rows:
            parts.append(" | ".join(
                cell.text.strip() for cell in row.cells
            ))

    text = "\n".join(parts)

    return [(text, "Word Document", 1)] if text.strip() else []


# Read PowerPoint PPTX
def read_pptx(path):

    presentation = Presentation(path)
    units = []

    for slide_no, slide in enumerate(presentation.slides, start=1):

        parts = []

        for shape in slide.shapes:

            if shape.has_text_frame:
                if shape.text.strip():
                    parts.append(shape.text)

            # Also read PowerPoint tables
            if shape.has_table:
                for row in shape.table.rows:
                    parts.append(" | ".join(
                        cell.text.strip() for cell in row.cells
                    ))

        text = "\n".join(parts)

        if text.strip():
            units.append((
                text,
                f"Slide {slide_no}",
                slide_no
            ))

    return units


# Read Excel XLSX
def read_xlsx(path):

    workbook = load_workbook(
        path,
        read_only=True,
        data_only=True
    )

    units = []

    try:
        for sheet in workbook.worksheets:

            rows = []

            for row in sheet.iter_rows(values_only=True):
                values = [
                    str(value) if value is not None else ""
                    for value in row
                ]

                if any(value.strip() for value in values):
                    rows.append(" | ".join(values))

            text = "\n".join(rows)

            if text.strip():
                units.append((
                    text,
                    f"Sheet: {sheet.title}",
                    1
                ))
    finally:
        workbook.close()

    return units


# Read CSV
def read_csv(path):

    with open(path, "r", encoding="utf-8-sig", newline="") as file:

        sample = file.read(4096)
        file.seek(0)

        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel

        reader = csv.reader(file, dialect)

        rows = [
            " | ".join(row)
            for row in reader
            if any(cell.strip() for cell in row)
        ]

    text = "\n".join(rows)

    return [(text, "CSV Document", 1)] if text.strip() else []


# Read TXT
def read_txt(path):

    try:
        with open(path, "r", encoding="utf-8-sig") as file:
            text = file.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as file:
            text = file.read()

    return [(text, "Text Document", 1)] if text.strip() else []


# Select the correct reader
def extract_document(path):

    extension = Path(path).suffix.lower()

    readers = {
        ".pdf": read_pdf,
        ".docx": read_docx,
        ".pptx": read_pptx,
        ".xlsx": read_xlsx,
        ".csv": read_csv,
        ".txt": read_txt
    }

    if extension not in readers:
        raise ValueError(
            f"Unsupported file format: {extension}"
        )

    return readers[extension](path)


# Process and store any supported document
def ingest_document(path):

    # Read document
    units = extract_document(path)

    if not units:
        return 0

    # Prepare chunks and metadata
    ids = []
    texts = []
    metadatas = []

    file_name = os.path.basename(path)

    for unit_no, (text, location, page_no) in enumerate(units):

        for chunk_no, chunk in enumerate(chunk_text(text)):

            chunk_id = f"{unit_no}-{chunk_no}"

            ids.append(chunk_id)
            texts.append(chunk)

            metadatas.append({
                "page": page_no,
                "location": location,
                "file_name": file_name,
                "file_type": Path(path).suffix.lower()
            })

    if not texts:
        return 0

    # Create embeddings
    embeddings = model.encode(texts).tolist()

    # Replace old document collection
    try:
        client.delete_collection("docs")
    except Exception:
        pass

    collection = client.create_collection("docs")

    # Store in ChromaDB
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return len(texts)


# Keep compatibility with older main.py
def ingest_pdf(path):
    return ingest_document(path)
