-- Função para buscar chunks por similaridade
CREATE OR REPLACE FUNCTION search_similar_chunks(
    query_vector vector(1536),
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INT DEFAULT 10
)
RETURNS TABLE (
    id INT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT,
    created_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dc.id,
        dc.content,
        dc.metadata,
        1 - (dc.embedding <=> query_vector) AS similarity,
        dc.created_at
    FROM document_chunks dc
    WHERE 1 - (dc.embedding <=> query_vector) > similarity_threshold
    ORDER BY dc.embedding <=> query_vector
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Função para buscar chunks por fonte
CREATE OR REPLACE FUNCTION get_chunks_by_source(
    source_pattern TEXT
)
RETURNS TABLE (
    id INT,
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dc.id,
        dc.content,
        dc.metadata,
        dc.created_at
    FROM document_chunks dc
    WHERE dc.metadata->>'source' ILIKE '%' || source_pattern || '%'
    ORDER BY (dc.metadata->>'chunk_id')::NUMERIC;
END;
$$ LANGUAGE plpgsql;

-- Função para estatísticas da tabela
CREATE OR REPLACE FUNCTION get_chunk_statistics()
RETURNS TABLE (
    total_chunks BIGINT,
    total_sources BIGINT,
    avg_chunk_length NUMERIC,
    oldest_chunk TIMESTAMP,
    newest_chunk TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) AS total_chunks,
        COUNT(DISTINCT metadata->>'source') AS total_sources,
        AVG(LENGTH(content)) AS avg_chunk_length,
        MIN(created_at) AS oldest_chunk,
        MAX(created_at) AS newest_chunk
    FROM document_chunks;
END;
$$ LANGUAGE plpgsql;
