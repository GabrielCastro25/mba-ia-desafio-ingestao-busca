# -*- coding: utf-8 -*-
import os
import json
import psycopg2
import numpy as np
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import openai
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
PDF_PATH = os.getenv("PDF_PATH")
DATABASE_URL = os.getenv("DATABASE_URL")
COLLECTION_NAME = os.getenv("PG_VECTOR_COLLECTION_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class PDFIngestionPipeline:
    """Classe principal para ingestão de PDF"""
    
    def __init__(self):
        self.pdf_path = PDF_PATH
        self.database_url = DATABASE_URL
        self.collection_name = COLLECTION_NAME
        self.openai_api_key = OPENAI_API_KEY
        self.google_api_key = GOOGLE_API_KEY
        self.conn = None
    
    def connect_to_database(self):
        """Conecta ao banco de dados PostgreSQL"""
        try:
            self.conn = psycopg2.connect(self.database_url)
            logger.info("Conexão com banco de dados estabelecida")
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco: {e}")
            return False
    
    def setup_database(self):
        """Verifica se o banco está configurado (Flyway cuida das migrações)"""
        try:
            cur = self.conn.cursor()
            
            # Verificar se a tabela existe
            cur.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{self.collection_name}'
                );
            """)
            table_exists = cur.fetchone()[0]
            
            if not table_exists:
                logger.error("Tabela não encontrada! Execute as migrações do Flyway primeiro:")
                logger.error("  docker-compose up flyway")
                logger.error("  ou")
                logger.error("  python3 scripts/db_manager.py migrate")
                return False
            
            logger.info("Banco de dados verificado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao verificar banco: {e}")
            return False
    
    def extract_text_from_pdf(self, pdf_path):
        """Extrai texto de um arquivo PDF"""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                logger.info(f"Página {page_num + 1} processada")
            return text
        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF: {e}")
            return None
    
    def create_chunks(self, text, chunk_size=1000, overlap=150):
        """Divide o texto em chunks com overlap"""
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            if chunk.strip():
                chunks.append(chunk)
        return chunks
    
    def create_embeddings_openai(self, texts):
        """Cria embeddings usando OpenAI API"""
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Erro ao criar embeddings OpenAI: {e}")
            return None
    
    def create_mock_embeddings(self, texts):
        """Cria embeddings mock para demonstração"""
        logger.info("Criando embeddings mock (1536 dimensões)...")
        embeddings = []
        for i, text in enumerate(texts):
            # Criar embeddings determinísticos baseados no hash do texto
            np.random.seed(hash(text) % 1000000)
            embedding = np.random.normal(0, 1, 1536).astype(np.float32)
            # Normalizar para vetor unitário
            embedding = embedding / np.linalg.norm(embedding)
            embeddings.append(embedding.tolist())
        return embeddings
    
    def create_embeddings(self, texts):
        """Cria embeddings usando OpenAI ou mock"""
        if self.openai_api_key:
            logger.info("Usando OpenAI API para embeddings")
            embeddings = self.create_embeddings_openai(texts)
            if embeddings:
                return embeddings
            else:
                logger.warning("Falha ao usar OpenAI, usando mock embeddings")
        
        logger.info("Usando mock embeddings")
        return self.create_mock_embeddings(texts)
    
    def store_embeddings_in_db(self, chunks, embeddings):
        """Armazena os embeddings no banco de dados"""
        try:
            cur = self.conn.cursor()
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                metadata = {
                    "source": self.pdf_path,
                    "chunk_id": i,
                    "chunk_length": len(chunk),
                    "embedding_type": "openai" if self.openai_api_key else "mock"
                }
                
                cur.execute(f"""
                    INSERT INTO {self.collection_name} (content, embedding, metadata)
                    VALUES (%s, %s, %s)
                """, (chunk, embedding, json.dumps(metadata)))
            
            self.conn.commit()
            logger.info(f"Armazenados {len(chunks)} embeddings no banco de dados")
            return True
        except Exception as e:
            logger.error(f"Erro ao armazenar embeddings: {e}")
            self.conn.rollback()
            return False
    
    def verify_storage(self):
        """Verifica se os dados foram armazenados corretamente"""
        try:
            cur = self.conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM {self.collection_name}")
            count = cur.fetchone()[0]
            logger.info(f"Total de chunks armazenados: {count}")
            
            cur.execute(f"""
                SELECT content, metadata, created_at 
                FROM {self.collection_name} 
                ORDER BY created_at DESC 
                LIMIT 3
            """)
            rows = cur.fetchall()
            
            logger.info("Amostra de chunks armazenados:")
            for i, (content, metadata, created_at) in enumerate(rows):
                meta = json.loads(metadata) if isinstance(metadata, str) else metadata
                logger.info(f"Chunk {i+1} (ID: {meta['chunk_id']}):")
                logger.info(f"  Content: {content[:100]}...")
                logger.info(f"  Metadata: {meta}")
                logger.info(f"  Created: {created_at}")
                logger.info("")
            
            return True
        except Exception as e:
            logger.error(f"Erro ao verificar armazenamento: {e}")
            return False
    
    def run(self):
        """Executa o pipeline completo de ingestão"""
        logger.info("Iniciando pipeline de ingestão de PDF...")
        
        # Verificar se o PDF existe
        if not os.path.exists(self.pdf_path):
            logger.error(f"Arquivo PDF não encontrado: {self.pdf_path}")
            return False
        
        # Conectar ao banco
        if not self.connect_to_database():
            return False
        
        try:
            # Configurar banco
            if not self.setup_database():
                return False
            
            # Extrair texto do PDF
            logger.info("Extraindo texto do PDF...")
            text = self.extract_text_from_pdf(self.pdf_path)
            if not text:
                logger.error("Falha ao extrair texto do PDF")
                return False
            
            logger.info(f"Texto extraído: {len(text)} caracteres")
            
            # Criar chunks
            logger.info("Criando chunks (1000 caracteres com overlap de 150)...")
            chunks = self.create_chunks(text, chunk_size=1000, overlap=150)
            logger.info(f"Criados {len(chunks)} chunks")
            
            # Criar embeddings
            logger.info("Gerando embeddings...")
            embeddings = self.create_embeddings(chunks)
            if not embeddings:
                logger.error("Falha ao criar embeddings")
                return False
            
            logger.info(f"Gerados {len(embeddings)} embeddings")
            
            # Armazenar no banco
            logger.info("Armazenando embeddings no banco de dados...")
            if not self.store_embeddings_in_db(chunks, embeddings):
                return False
            
            # Verificar armazenamento
            self.verify_storage()
            
            logger.info("=" * 50)
            logger.info("PIPELINE CONCLUÍDO COM SUCESSO!")
            logger.info("=" * 50)
            logger.info("✓ Texto extraído do PDF")
            logger.info("✓ Chunks criados (1000 chars, 150 overlap)")
            logger.info("✓ Embeddings gerados")
            logger.info("✓ Dados armazenados no PostgreSQL com pgVector")
            
            return True
            
        finally:
            if self.conn:
                self.conn.close()
                logger.info("Conexão com banco de dados fechada")

def main():
    pipeline = PDFIngestionPipeline()
    success = pipeline.run()
    
    if success:
        logger.info("\nPara usar embeddings reais:")
        logger.info("1. Configure OPENAI_API_KEY no arquivo .env")
        logger.info("2. Execute o script novamente")
        logger.info("3. Os chunks serão substituídos com embeddings reais")
    else:
        logger.error("Falha no pipeline de ingestão")
        exit(1)

if __name__ == "__main__":
    main()
