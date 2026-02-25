# PDF Ingestion Pipeline

Pipeline completo para ingestão de PDFs com armazenamento vetorial no PostgreSQL + pgVector.

## 🚀 Funcionalidades

- ✅ **Extração de texto** de arquivos PDF
- ✅ **Chunking inteligente** (1000 caracteres com overlap de 150)
- ✅ **Geração de embeddings** (OpenAI API ou mock)
- ✅ **Armazenamento vetorial** com pgVector
- ✅ **Gestão de migrações** com Flyway
- ✅ **Busca por similaridade** pronta para usar

## 📋 Pré-requisitos

- Docker e Docker Compose
- Python 3.8+
- OpenAI API Key (opcional)

## 🛠️ Setup Rápido

### 1. Subir a infraestrutura

```bash
# Inicia PostgreSQL + pgVector + Flyway
docker-compose up -d

# Executa as migrações do banco
docker-compose up flyway
```

### 2. Configurar ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas configurações
# OPENAI_API_KEY=sua_chave_aqui
# PDF_PATH=document.pdf
```

### 3. Instalar dependências Python

```bash
pip3 install -r requirements.txt
```

### 4. Executar a ingestão

```bash
python3 src/ingest.py
```

## 📁 Estrutura do Projeto

```
├── src/
│   └── ingest.py              # Pipeline principal de ingestão
├── scripts/
│   └── db_manager.py          # Utilitário para gestão do banco
├── migrations/
│   └── sql/                   # Migrações Flyway
│       ├── V001__Create_vector_extension.sql
│       ├── V002__Create_document_chunks_table.sql
│       └── V003__Create_search_functions.sql
├── docker-compose.yml         # Infraestrutura Docker
├── requirements.txt           # Dependências Python
└── document.pdf              # PDF de exemplo
```

## 🗄️ Gestão do Banco de Dados

### Usando o script utilitário:

```bash
# Verificar status das migrações
python3 scripts/db_manager.py status

# Executar migrações pendentes
python3 scripts/db_manager.py migrate

# Verificar informações do schema
python3 scripts/db_manager.py info

# Limpar banco (apenas desenvolvimento)
python3 scripts/db_manager.py clean

# Verificar conexão
python3 scripts/db_manager.py check
```

### Usando Docker diretamente:

```bash
# Executar migrações
docker-compose up flyway

# Verificar logs
docker-compose logs flyway
```

## 🔍 Busca por Similaridade

O pipeline cria funções úteis para busca:

```sql
-- Buscar chunks similares a um vetor
SELECT * FROM search_similar_chunks(
    '[0.1, 0.2, 0.3, ...]'::vector(1536),
    0.7,  -- threshold de similaridade
    10    -- máximo de resultados
);

-- Buscar chunks por fonte
SELECT * FROM get_chunks_by_source('document.pdf');

-- Estatísticas dos chunks
SELECT * FROM get_chunk_statistics();
```

## 📊 Exemplo de Uso

### 1. Ingestão Básica

```python
from src.ingest import PDFIngestionPipeline

pipeline = PDFIngestionPipeline()
success = pipeline.run()
```

### 2. Com Embeddings Reais

Configure sua OpenAI API Key no `.env`:

```bash
OPENAI_API_KEY=sk-...
```

O pipeline automaticamente usará embeddings reais em vez de mocks.

### 3. Verificação dos Dados

```python
import psycopg2

conn = psycopg2.connect("postgresql://postgres:postgres@127.0.0.1:5432/rag")
cur = conn.cursor()

# Contar chunks
cur.execute("SELECT COUNT(*) FROM document_chunks")
count = cur.fetchone()[0]
print(f"Total chunks: {count}")

# Buscar amostra
cur.execute("SELECT content, metadata FROM document_chunks LIMIT 3")
for row in cur.fetchall():
    print(f"Content: {row[0][:100]}...")
    print(f"Metadata: {row[1]}")
```

## 🔄 Fluxo de Trabalho

1. **Desenvolvimento**: Use mock embeddings para testes rápidos
2. **Produção**: Configure OPENAI_API_KEY para embeddings reais
3. **Migrações**: Use Flyway para gerenciar alterações no schema
4. **Monitoramento**: Use as funções de busca e estatísticas

## 🐛 Troubleshooting

### Problemas Comuns

**Banco não conecta:**
```bash
# Verificar se PostgreSQL está rodando
docker ps | grep postgres

# Verificar logs
docker-compose logs postgres
```

**Migrações falham:**
```bash
# Limpar e reexecutar
python3 scripts/db_manager.py clean
python3 scripts/db_manager.py migrate
```

**Python 2.7 detectado:**
```bash
# Use python3 explicitamente
python3 src/ingest.py
```

### Logs Detalhados

O pipeline inclui logging detalhado. Para mais informações:

```bash
# Ver logs em tempo real
python3 src/ingest.py 2>&1 | tee ingestion.log
```

## 🚀 Próximos Passos

- [ ] Implementar interface web para busca
- [ ] Adicionar suporte a múltiplos formatos de documento
- [ ] Implementar cache de embeddings
- [ ] Adicionar métricas e monitoramento
- [ ] Implementar reprocessamento incremental

## 📝 Licença

MIT License - sinta-se livre para usar e modificar!