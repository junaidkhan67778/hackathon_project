from typing import List
import PyPDF2
import docx
from sentence_transformers import SentenceTransformer
import numpy as np

embedding_model = None

def init_model():
    global embedding_model
    if embedding_model is None:
        # valid, 384-dim, English, free
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def extract_text_pdf(file_path: str) -> str:
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    except Exception:
        pass
    return text

def extract_text_docx(file_path: str) -> str:
    try:
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception:
        return ""

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    chunks, start = [], 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def semantic_search(query: str, documents: List[dict], embeddings: List[np.ndarray], top_k: int = 3) -> List[dict]:
    if not documents:
        return []
    init_model()
    query_emb = embedding_model.encode([query])[0]
    similarities = []
    for idx, emb in enumerate(embeddings):
        sim = np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb))
        similarities.append((sim, idx))
    similarities.sort(reverse=True)
    return [documents[idx] for _, idx in similarities[:top_k]]
