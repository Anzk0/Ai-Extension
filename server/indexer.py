import fitz  # PyMuPDF
import os
import chromadb
from sentence_transformers import SentenceTransformer

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    if not words:
        return []
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


def extract_text_from_pdf(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def index_vault(vault_path, collection_name="vault"):
    client = chromadb.Client()
    collection = client.get_or_create_collection(collection_name)
    model = get_model()

    for filename in os.listdir(vault_path):
        filepath = os.path.join(vault_path, filename)
        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(filepath)
        elif filename.endswith(".txt") or filename.endswith(".md"):
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            continue

        chunks = chunk_text(text)
        if not chunks:
            continue

        embeddings = model.encode(chunks).tolist()
        ids = [f"{filename}_chunk_{i}" for i in range(len(chunks))]
        collection.add(documents=chunks, embeddings=embeddings, ids=ids)

    return collection
