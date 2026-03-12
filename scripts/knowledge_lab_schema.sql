-- Habilitar extensão pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabela de documentos do Knowledge Lab
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id VARCHAR(255) NOT NULL,
    document_name VARCHAR(255) NOT NULL,
    document_type VARCHAR(50) DEFAULT 'custom', -- product_manual, pricing, faq, process, custom
    file_path VARCHAR(512),
    file_size_mb DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'indexed', -- indexed, processing, failed, archived
    chunks_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_company_id (company_id),
    INDEX idx_document_type (document_type),
    INDEX idx_created_at (created_at)
);

-- Tabela de chunks com embeddings (pgvector)
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    chunk_number INTEGER,
    chunk_text TEXT NOT NULL,
    chunk_length INTEGER,
    tokens_count INTEGER,
    embedding vector(1536), -- OpenAI text-embedding-3-small
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    INDEX idx_document_id (document_id)
);

-- Criar índice para busca vetorial rápida (IVFFlat)
CREATE INDEX IF NOT EXISTS knowledge_chunks_embedding_idx 
ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Tabela de queries (histórico de buscas)
CREATE TABLE IF NOT EXISTS knowledge_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id VARCHAR(255) NOT NULL,
    conversation_id UUID,
    contact_id VARCHAR(255),
    query_text TEXT NOT NULL,
    response_text TEXT,
    source_document_id UUID REFERENCES knowledge_documents(id) ON DELETE SET NULL,
    confidence DECIMAL(3, 2),
    was_helpful BOOLEAN,
    feedback_text TEXT,
    chunks_used INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_company_id (company_id),
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_created_at (created_at),
    INDEX idx_was_helpful (was_helpful)
);

-- Tabela de configurações do Knowledge Lab
CREATE TABLE IF NOT EXISTS knowledge_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id VARCHAR(255) NOT NULL UNIQUE,
    temperature DECIMAL(2, 1) DEFAULT 0.3,
    max_context_length INTEGER DEFAULT 2000,
    top_k_chunks INTEGER DEFAULT 3,
    similarity_threshold DECIMAL(3, 2) DEFAULT 0.5,
    enable_rag BOOLEAN DEFAULT TRUE,
    enable_feedback BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_company_id (company_id)
);

-- View para análise de documentos
CREATE OR REPLACE VIEW knowledge_documents_stats AS
SELECT 
    d.company_id,
    d.id,
    d.document_name,
    d.document_type,
    d.chunks_count,
    COUNT(c.id) AS actual_chunks,
    d.created_at,
    d.status
FROM knowledge_documents d
LEFT JOIN knowledge_chunks c ON d.id = c.document_id
GROUP BY d.company_id, d.id, d.document_name, d.document_type, d.chunks_count, d.created_at, d.status;

-- View para análise de queries
CREATE OR REPLACE VIEW knowledge_queries_stats AS
SELECT 
    company_id,
    DATE(created_at) AS query_date,
    COUNT(*) AS total_queries,
    SUM(CASE WHEN was_helpful = TRUE THEN 1 ELSE 0 END) AS helpful_queries,
    AVG(CAST(was_helpful AS INTEGER)) AS helpful_rate,
    AVG(response_time_ms) AS avg_response_time_ms,
    AVG(confidence) AS avg_confidence
FROM knowledge_queries
GROUP BY company_id, DATE(created_at);

-- Trigger para atualizar updated_at
CREATE OR REPLACE FUNCTION update_knowledge_documents_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_knowledge_documents_update
BEFORE UPDATE ON knowledge_documents
FOR EACH ROW
EXECUTE FUNCTION update_knowledge_documents_timestamp();

CREATE TRIGGER trigger_knowledge_settings_update
BEFORE UPDATE ON knowledge_settings
FOR EACH ROW
EXECUTE FUNCTION update_knowledge_documents_timestamp();

-- Seed data (opcional)
INSERT INTO knowledge_settings (company_id, temperature, max_context_length, top_k_chunks, similarity_threshold)
VALUES 
    ('demo_company', 0.3, 2000, 3, 0.5),
    ('test_company', 0.2, 1500, 5, 0.6)
ON CONFLICT (company_id) DO NOTHING;
