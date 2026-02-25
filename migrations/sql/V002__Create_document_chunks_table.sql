-- Criar tabela para armazenar chunks de documentos com embeddings
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criar índice para busca por similaridade usando IVFFlat
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
ON document_chunks 
USING ivfflat (embedding vector_cosine_ops);

-- Criar índices para metadados comuns
CREATE INDEX IF NOT EXISTS document_chunks_source_idx 
ON document_chunks 
USING btree ((metadata->>'source'));

CREATE INDEX IF NOT EXISTS document_chunks_chunk_id_idx 
ON document_chunks 
USING btree ((metadata->>'chunk_id'));

-- Criar trigger para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_document_chunks_updated_at 
    BEFORE UPDATE ON document_chunks 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
