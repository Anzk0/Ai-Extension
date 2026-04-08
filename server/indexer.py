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
    if overlap >= chunk_size:
        raise ValueError(f"overlap ({overlap}) must be less than chunk_size ({chunk_size})")
    words = text.split()
    if not words:
        return []
    step = chunk_size - overlap
    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), step)]
    # Drop tiny tail chunks (smaller than overlap) unless it's the only chunk
    return [c for c in chunks if len(c.split()) > overlap] or chunks[:1]


def extract_text_from_pdf(path):
    with fitz.open(path) as doc:
        return "".join(page.get_text() for page in doc)


def index_vault(vault_path, chroma_db_path):
    client = chromadb.PersistentClient(path=chroma_db_path)
    collection = client.get_or_create_collection('vault')
    model = get_model()
    indexed = 0

    for topic in os.listdir(vault_path):
        topic_path = os.path.join(vault_path, topic)
        if not os.path.isdir(topic_path):
            continue
        for filename in os.listdir(topic_path):
            if not filename.endswith('.pdf'):
                continue
            pdf_path = os.path.join(topic_path, filename)
            try:
                text = extract_text_from_pdf(pdf_path)
                chunks = chunk_text(text)
                for i, chunk in enumerate(chunks):
                    embedding = model.encode(chunk).tolist()
                    doc_id = f"{topic}__{filename}__{i}"
                    collection.upsert(
                        ids=[doc_id],
                        embeddings=[embedding],
                        documents=[chunk],
                        metadatas=[{
                            'topic': topic,
                            'filename': filename,
                            'chunk_index': i
                        }]
                    )
                    indexed += 1
            except Exception as e:
                print(f"[indexer] Failed to index {pdf_path}: {e}")

    return {'indexed': indexed}
