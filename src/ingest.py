import os
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from openai import RateLimitError

load_dotenv()

PDF_PATH = os.getenv("PDF_PATH")
DATABASE_URL = os.getenv("DATABASE_URL")
COLLECTION_NAME = os.getenv("PG_VECTOR_COLLECTION_NAME")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL")

BATCH_SIZE = 10
MAX_RETRIES = 3
RETRY_DELAY = 60  # segundos entre tentativas após rate limit


def add_documents_with_retry(vectorstore, batch, batch_num):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            vectorstore.add_documents(batch)
            return
        except RateLimitError as e:
            error_code = getattr(e, "code", None) or (
                e.body.get("error", {}).get("code") if hasattr(e, "body") and e.body else None
            )
            if error_code == "insufficient_quota":
                raise RuntimeError(
                    "Cota da API OpenAI esgotada. Adicione créditos em "
                    "https://platform.openai.com/account/billing"
                ) from e
            if attempt < MAX_RETRIES:
                print(
                    f"  Rate limit atingido no lote {batch_num} "
                    f"(tentativa {attempt}/{MAX_RETRIES}). "
                    f"Aguardando {RETRY_DELAY}s..."
                )
                time.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(
                    f"Rate limit persistente após {MAX_RETRIES} tentativas no lote {batch_num}."
                ) from e


def ingest_pdf():
    print(f"Carregando PDF: {PDF_PATH}")
    loader = PyPDFLoader(PDF_PATH)
    documents = loader.load()
    print(f"{len(documents)} página(s) carregada(s).")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(documents)
    print(f"{len(chunks)} chunk(s) gerado(s).")

    embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)

    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=DATABASE_URL,
    )

    total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"  Enviando lote {batch_num}/{total_batches} ({len(batch)} chunks)...")
        add_documents_with_retry(vectorstore, batch, batch_num)

    print("Ingestão concluída com sucesso.")


if __name__ == "__main__":
    try:
        ingest_pdf()
    except RuntimeError as e:
        print(f"\nErro: {e}")
        exit(1)
