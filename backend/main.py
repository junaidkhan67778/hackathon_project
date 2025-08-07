from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import shutil, os, uuid, json, time, re, logging, asyncio
from concurrent.futures import ThreadPoolExecutor
from sentence_transformers import SentenceTransformer
import numpy as np
import PyPDF2, docx
import google.generativeai as genai

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Environment-based CORS configuration
allowed_origins = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "https://hackathonproject-to7y7xnbyepyehmwme3xry.streamlit.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"]
)

documents, embeddings = [], []
embedding_model = None
MAX_DOCUMENTS = 1000

# Validate API key exists
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.error("GOOGLE_API_KEY environment variable is required")
    raise ValueError("GOOGLE_API_KEY environment variable is required")
genai.configure(api_key=api_key)

class QueryRequest(BaseModel):
    query: str
    policy_number: Optional[str] = ""

class ClaimResponse(BaseModel):
    claim_id: str
    decision: str
    amount: Optional[float] = None
    justification: str
    confidence_score: float
    processing_time: float

def init_model():
    global embedding_model
    if embedding_model is None:
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def cleanup_old_documents():
    global documents, embeddings
    if len(documents) > MAX_DOCUMENTS:
        logger.info(f"Cleaning up old documents. Current count: {len(documents)}")
        documents = documents[-MAX_DOCUMENTS:]
        embeddings = embeddings[-MAX_DOCUMENTS:]

def extract_text_pdf(path: str) -> str:
    text = ""
    try:
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    except PyPDF2.PdfReadError as e:
        logger.error(f"PDF reading failed for {path}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error reading PDF {path}: {e}")
    return text

def extract_text_docx(path: str) -> str:
    try:
        doc = docx.Document(path)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        logger.error(f"DOCX reading failed for {path}: {e}")
        return ""

def chunk_text(text: str, chunk_size: int=1000, overlap: int=200) -> List[str]:
    chunks, start = [], 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def _process_document_sync(document_id: str, path: str, filename: str):
    """Synchronous version for thread executor"""
    if filename.lower().endswith('.pdf'):
        text = extract_text_pdf(path)
    elif filename.lower().endswith('.docx'):
        text = extract_text_docx(path)
    else:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            logger.error(f"Text file reading failed for {path}: {e}")
            text = ""
    
    if not text.strip():
        logger.warning(f"No text extracted from {filename}")
        return
    
    init_model()
    chunks = chunk_text(text)
    embeddings_local = embedding_model.encode(chunks)
    
    for chunk, emb in zip(chunks, embeddings_local):
        documents.append({
            "id": f"{document_id}_{len(documents)}",
            "content": chunk,
            "filename": filename,
            "document_id": document_id
        })
        embeddings.append(emb)
    
    cleanup_old_documents()
    logger.info(f"Processed {filename}: {len(chunks)} chunks created")

async def process_document(document_id: str, path: str, filename: str):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        await loop.run_in_executor(executor, _process_document_sync, document_id, path, filename)

def semantic_search(query: str, top_k: int=5) -> List[dict]:
    if not documents: 
        return []
    
    init_model()
    query_emb = embedding_model.encode([query])[0]
    similarities = []
    
    for idx, emb in enumerate(embeddings):
        sim = np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb))
        similarities.append((sim, idx))
    
    similarities.sort(reverse=True)
    return [
        {
            "content": documents[idx]["content"],
            "filename": documents[idx]["filename"],
            "similarity": float(sim)
        }
        for sim, idx in similarities[:top_k]
    ]

def extract_and_parse_json(text: str) -> dict:
    """Robust JSON extraction from AI response"""
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'```\s*$', '', text.strip())
    
    # Try to find JSON object
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
    
    # Fallback: try parsing the entire text as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"Could not parse AI response as JSON: {text[:100]}...")
        return {"coverage": "REVIEW", "reason": "Could not parse AI response"}

@app.post("/upload-document")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        os.makedirs("uploads", exist_ok=True)
        document_id = str(uuid.uuid4())
        path = os.path.join("uploads", f"{document_id}_{file.filename}")
        
        with open(path, "wb") as out:
            shutil.copyfileobj(file.file, out)
        
        background_tasks.add_task(process_document, document_id, path, file.filename)
        return {
            "document_id": document_id, 
            "status": "processing",
            "filename": file.filename
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-claim", response_model=ClaimResponse)
async def process_claim(request: QueryRequest):
    start = time.time()
    
    try:
        relevant_docs = semantic_search(request.query, top_k=5)
        context = "\n---\n".join([d["content"] for d in relevant_docs])
        
        prompt = f"""You are an insurance expert. Give a SHORT answer (max 2 sentences).

Claim: {request.query}

Policy: {context}

Return ONLY JSON:
{{
  "coverage": "COVERED" | "NOT COVERED" | "REVIEW",
  "reason": "Brief 1-2 sentence explanation with specific policy reference"
}}

Keep the reason under 30 words."""
        
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config={"max_output_tokens": 100}
)

        response = model.generate_content(prompt)
        text = response.text.strip()
        
        parsed = extract_and_parse_json(text)
        
        # Validate coverage decision
        coverage = parsed.get("coverage", "REVIEW").upper()
        if coverage not in ["COVERED", "NOT COVERED", "REVIEW"]:
            coverage = "REVIEW"
        
        end = time.time()
        
        return ClaimResponse(
            claim_id=f"CLAIM-{uuid.uuid4()}",
            decision=coverage,
            amount=None,
            justification=parsed.get("reason", "No explanation available"),
            confidence_score=0.85,
            processing_time=end - start
        )
        
    except Exception as e:
        logger.error(f"Claim processing failed: {e}")
        end = time.time()
        return ClaimResponse(
            claim_id=f"CLAIM-{uuid.uuid4()}",
            decision="REVIEW",
            amount=None,
            justification=f"Processing error: {str(e)}",
            confidence_score=0.0,
            processing_time=end - start
        )

@app.get("/")
def root():
    return {"message": "Backend is alive"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "processed_documents": len(documents),
        "total_chunks": len(embeddings),
        "embedding_model_loaded": embedding_model is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
