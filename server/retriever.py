import chromadb
from sentence_transformers import SentenceTransformer

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def retrieve_chunks(question, topic, chroma_db_path, n_results=5):
    client = chromadb.PersistentClient(path=chroma_db_path)
    try:
        collection = client.get_collection('vault')
    except Exception:
        return []

    model = get_model()
    embedding = model.encode(question).tolist()

    try:
        results = collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where={'topic': topic}
        )
    except Exception:
        return []

    chunks = []
    if results['documents'] and results['documents'][0]:
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            chunks.append({
                'text': doc,
                'filename': meta['filename'],
                'topic': meta['topic']
            })
    return chunks
