"""
Knowledge Lab - RAG endpoints para Vexus CRM
Permite upload de documentos e busca vetorial com pgvector
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends, Body
from fastapi.responses import JSONResponse
import os
import json
from typing import List, Optional
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    PyPDF2 = None
import logging
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session

from vexus_crm.database import get_db
from vexus_crm.models import KnowledgeDocument

logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    query: str
    company_id: Optional[str] = None
    conversation_id: Optional[str] = None
    contact_id: Optional[str] = None
    top_k: int = 3

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Lab"])

# Mock embeddings (em produção, usar OpenAI)
def get_mock_embedding(text: str) -> List[float]:
    """Gera embedding mock (em produção: use OpenAI)"""
    import hashlib
    import struct
    # Gerar pseudo-random vector de 1536 dimensões baseado no hash do texto
    hash_obj = hashlib.md5(text.encode())
    seed = struct.unpack('I', hash_obj.digest()[:4])[0]
    import random
    random.seed(seed)
    return [random.uniform(-1, 1) for _ in range(1536)]


# Configuração upload
UPLOAD_DIR = "/tmp/knowledge_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    company_id: str = None,
    doc_type: str = "custom"
):
    """
    Faz upload de um documento (PDF, DOCX) e indexa para RAG
    
    Args:
        file: Arquivo PDF ou DOCX
        company_id: ID da empresa
        doc_type: Tipo do documento (product_manual, pricing, faq, process, custom)
    
    Returns:
        Status do upload e número de chunks indexados
    """
    try:
        # 1. Validar arquivo
        if not file.filename:
            raise HTTPException(status_code=400, detail="Arquivo inválido")
        
        # 2. Salvar arquivo temporário
        temp_file = f"{UPLOAD_DIR}/{file.filename}"
        contents = await file.read()
        
        with open(temp_file, "wb") as f:
            f.write(contents)
        
        # 3. Extrair texto do PDF
        text = ""
        if file.filename.endswith(".pdf"):
            if not HAS_PYPDF2:
                raise HTTPException(status_code=400, detail="PDF processing não disponível. PyPDF2 não instalado.")
            try:
                with open(temp_file, "rb") as pdf:
                    reader = PyPDF2.PdfReader(pdf)
                    for page in reader.pages:
                        text += page.extract_text()
            except Exception as e:
                logger.error(f"Erro ao extrair PDF: {e}")
                raise HTTPException(status_code=400, detail="Erro ao processar PDF")
        else:
            raise HTTPException(status_code=400, detail="Apenas arquivos PDF são suportados")
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="PDF vazio ou protegido")
        
        # 4. Dividir em chunks (simple implementation sem langchain)
        def split_text(text, chunk_size=500, chunk_overlap=50):
            """Simple text splitter without langchain dependency"""
            chunks = []
            words = text.split()
            current_chunk = []
            
            for word in words:
                current_chunk.append(word)
                if len(" ".join(current_chunk)) >= chunk_size:
                    chunks.append(" ".join(current_chunk))
                    # Overlap para contexto
                    current_chunk = current_chunk[-int(chunk_overlap/10):]
            
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            
            return chunks
        
        chunks = split_text(text)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="Não foi possível extrair conteúdo")
        
        # 5. Criar embeddings
        embeddings_list = []
        for i, chunk in enumerate(chunks):
            embedding = get_mock_embedding(chunk)
            embeddings_list.append({
                "chunk_number": i,
                "chunk_text": chunk,
                "embedding": embedding,
                "tokens": len(chunk.split())
            })
        
        # 6. Salvar no banco de dados real
        db: Session = next(get_db())
        doc = KnowledgeDocument(
            company_id=company_id,
            document_name=file.filename,
            document_type=doc_type,
            file_size_mb=len(contents) / (1024 * 1024),
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        for i, chunk in enumerate(chunks):
            emb = get_mock_embedding(chunk)
            # Store chunk data (KnowledgeChunk model)
            chunk_data = {
                "document_id": doc.id,
                "chunk_number": i,
                "chunk_text": chunk,
                "embedding": emb,
                "tokens": len(chunk.split()),
            }
            db.add(kc)
        db.commit()
        os.remove(temp_file)
        logger.info(f"Documento '{file.filename}' indexado com {len(chunks)} chunks")
        return {
            "status": "success",
            "document_id": doc.id,
            "chunks_indexed": len(chunks),
            "file_size_mb": round(len(contents) / (1024 * 1024), 2),
            "message": f"Documento '{file.filename}' indexado com sucesso!"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao fazer upload: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao fazer upload: {str(e)}")


@router.post("/query")
async def query_knowledge_base(
    request_body: QueryRequest | None = Body(None),
    query: str | None = Query(None),
    company_id: str | None = Query(None),
    top_k: int = Query(3),
    db: Session = Depends(get_db)
):
    """
    Faz uma pergunta ao Knowledge Base e retorna resposta com fonte
    """
    try:
        # suportar tanto body JSON (QueryRequest) quanto query params (tests usam params)
        if request_body is not None:
            request = request_body
        else:
            if not query:
                raise HTTPException(status_code=400, detail="Parâmetro 'query' é obrigatório")
            request = QueryRequest(query=query, company_id=company_id, top_k=top_k)

        # 1. Criar embedding da pergunta
        query_embedding = get_mock_embedding(request.query)

        # 2. Acessar banco de dados
        docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.company_id == request.company_id).all() if request.company_id else []
        if not docs:
            return {
                "query": request.query,
                "response": "Nenhum documento foi indexado ainda. Faça upload de PDFs para começar.",
                "source_document": None,
                "confidence": 0.0,
                "use_knowledge_base": False,
                "chunks_used": 0
            }
        
        def cosine_similarity(a, b):
            import math
            dot = sum(x * y for x, y in zip(a, b))
            mag_a = math.sqrt(sum(x**2 for x in a))
            mag_b = math.sqrt(sum(x**2 for x in b))
            if mag_a == 0 or mag_b == 0:
                return 0
            return dot / (mag_a * mag_b)
        
        results = []
        for doc in docs:
            for chunk in doc.chunks:
                sim = cosine_similarity(query_embedding, chunk.embedding)
                if sim > 0.2:
                    results.append((sim, doc, chunk))
        results.sort(key=lambda x: x[0], reverse=True)
        top = results[:request.top_k]
        if not top:
            return {
                "query": request.query,
                "response": f"Nenhuma informação encontrada para '{request.query}'",
                "source_document": None,
                "confidence": 0.0,
                "use_knowledge_base": True,
                "chunks_used": 0
            }
        sim, doc, chunk = top[0]
        return {
            "query": request.query,
            "response": chunk.chunk_text,
            "source_document": doc.document_name,
            "confidence": sim,
            "use_knowledge_base": True,
            "chunks_used": len(results)
        }
    
    except Exception as e:
        logger.error(f"Knowledge query error: {e}")
        return {
            "query": request.query,
            "response": "Erro ao processar a pergunta.",
            "error": str(e),
            "source_document": None,
            "confidence": 0.0,
            "use_knowledge_base": False,
            "chunks_used": 0
        }
        logger.error(f"Erro ao fazer query: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar query: {str(e)}")



@router.get("/documents")
async def list_documents(company_id: str):
    """Lista todos os documentos indexados da empresa"""
    try:
        db_file = f"{UPLOAD_DIR}/{company_id}_db.json"
        
        if not os.path.exists(db_file):
            return {"documents": [], "total": 0}
        
        with open(db_file, "r") as f:
            db_data = json.load(f)
        
        documents = []
        for doc_id, doc in db_data.items():
            documents.append({
                "id": doc_id,
                "name": doc["document_name"],
                "type": doc["document_type"],
                "chunks": doc["chunks_count"],
                "size_mb": round(doc["file_size_mb"], 2),
                "created_at": doc["created_at"]
            })
        
        return {
            "documents": documents,
            "total": len(documents)
        }
    
    except Exception as e:
        logger.error(f"Erro ao listar documentos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
async def delete_document(company_id: str, document_id: str):
    """Deleta um documento e seus chunks"""
    try:
        db_file = f"{UPLOAD_DIR}/{company_id}_db.json"
        
        if not os.path.exists(db_file):
            raise HTTPException(status_code=404, detail="Documento não encontrado")
        
        with open(db_file, "r") as f:
            db_data = json.load(f)
        
        if document_id in db_data:
            del db_data[document_id]
            
            with open(db_file, "w") as f:
                json.dump(db_data, f)
            
            return {"status": "deleted", "document_id": document_id}
        else:
            raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar documento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query-history")
async def get_query_history(
    company_id: str,
    limit: int = Query(50, le=1000)
):
    """Retorna histórico de queries para análise"""
    try:
        log_file = f"{UPLOAD_DIR}/{company_id}_queries.json"
        
        if not os.path.exists(log_file):
            return {"query_history": [], "total": 0}
        
        with open(log_file, "r") as f:
            queries = json.load(f)
        
        # Ordenar por timestamp decrescente e pegar últimas N
        queries.sort(key=lambda x: x["timestamp"], reverse=True)
        queries = queries[:limit]
        
        return {
            "query_history": queries,
            "total": len(queries)
        }
    
    except Exception as e:
        logger.error(f"Erro ao buscar histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Verifica saúde do Knowledge Lab"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "upload_dir": UPLOAD_DIR,
        "storage_available": True
    }
