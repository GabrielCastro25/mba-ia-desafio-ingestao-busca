# PDF Ingestion & Search Pipeline

Pipeline completo para ingestão de PDFs com armazenamento vetorial no PostgreSQL + pgVector e interface de chat.

## Funcionalidades

- Extração de texto de arquivos PDF
- Chunking inteligente (1000 caracteres com overlap de 150)
- Geração de embeddings via OpenAI
- Armazenamento vetorial com pgVector (via langchain-postgres)
- Busca por similaridade semântica
- Interface de chat RAG (Retrieval-Augmented Generation)

## Pré-requisitos

- Docker e Docker Compose
- Python 3.8+
- OpenAI API Key

## Setup

### 1. Subir a infraestrutura

```bash
docker-compose up -d
```

Isso inicia o PostgreSQL com a extensão pgVector. A criação das tabelas é gerenciada automaticamente pelo `langchain-postgres` na primeira execução.

### 2. Configurar o ambiente

```bash
cp ".env copy.example" .env
```

Edite o `.env` com suas configurações:

```env
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/rag
PG_VECTOR_COLLECTION_NAME=documents
PDF_PATH=document.pdf
```

### 3. Instalar Python 3.11

**macOS (Homebrew):**
```bash
brew install python@3.11
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install python3.11 python3.11-venv
```

**Windows:** Baixe o instalador em https://www.python.org/downloads/release/python-3110/

### 4. Criar e ativar o ambiente virtual

```bash
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 5. Instalar dependências Python

```bash
pip install -r requirements.txt
```

### 6. Executar a ingestão

```bash
python src/ingest.py
```

O pipeline carrega o PDF, divide em chunks, gera embeddings e salva no banco.

### 7. Iniciar o chat

```bash
python src/chat.py
```

Digite suas perguntas sobre o conteúdo do PDF. Para encerrar, digite `sair`.

## Estrutura do Projeto

```
├── src/
│   ├── ingest.py   # Pipeline de ingestão de PDF
│   ├── search.py   # Lógica de busca e geração de resposta
│   └── chat.py     # Interface de chat interativa
├── docker-compose.yml      # PostgreSQL + pgVector
├── requirements.txt        # Dependências Python
├── .env copy.example       # Exemplo de variáveis de ambiente
└── document.pdf            # PDF de exemplo
```

## Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `OPENAI_API_KEY` | Sim | Chave da API OpenAI |
| `DATABASE_URL` | Sim | URL de conexão PostgreSQL |
| `PG_VECTOR_COLLECTION_NAME` | Sim | Nome da coleção no pgVector |
| `PDF_PATH` | Sim | Caminho para o arquivo PDF |
| `OPENAI_EMBEDDING_MODEL` | Não | Padrão: `text-embedding-3-small` |
| `GOOGLE_API_KEY` | Não | Chave da API Google (uso futuro) |
| `GOOGLE_EMBEDDING_MODEL` | Não | Padrão: `models/embedding-001` |


## Troubleshooting

**Banco não conecta:**
```bash
docker ps | grep postgres
docker-compose logs postgres
```

**Cota da API OpenAI esgotada:**

O script trata erros de `insufficient_quota` e exibe uma mensagem clara. Adicione créditos em https://platform.openai.com/account/billing e tente novamente.

**Rate limit:**

O pipeline faz até 3 tentativas com espera de 60 segundos entre elas antes de interromper.

**`chat.py` não encontra o módulo `search`:**
```bash
python src/chat.py
```
