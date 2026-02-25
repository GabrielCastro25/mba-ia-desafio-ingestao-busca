#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Manager Utility
========================

Script para gerenciar migrações e operações do banco de dados.
"""

import os
import sys
import subprocess
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/rag")

def run_flyway_command(command):
    """Executa comando Flyway usando Docker"""
    try:
        cmd = [
            "docker", "run", "--rm",
            "--network", "mba-ia-desafio-ingestao-busca_default",
            "-v", f"{os.getcwd()}/migrations/sql:/flyway/sql",
            "flyway/flyway:latest",
            "-url=jdbc:postgresql://postgres:5432/rag",
            "-user=postgres",
            "-password=postgres",
            "-locations=filesystem:/flyway/sql",
            command
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_database_connection():
    """Verifica conexão com o banco"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        conn.close()
        return True, version
    except Exception as e:
        return False, str(e)

def get_migration_status():
    """Verifica status das migrações"""
    success, stdout, stderr = run_flyway_command("info")
    if success:
        return True, stdout
    else:
        return False, stderr

def migrate_database():
    """Executa migrações pendentes"""
    success, stdout, stderr = run_flyway_command("migrate")
    if success:
        return True, stdout
    else:
        return False, stderr

def clean_database():
    """Limpa todas as migrações (cuidado: uso apenas em desenvolvimento)"""
    success, stdout, stderr = run_flyway_command("clean")
    if success:
        return True, stdout
    else:
        return False, stderr

def show_schema_info():
    """Mostra informações do schema"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Verificar tabelas
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        
        # Verificar extensões
        cur.execute("""
            SELECT extname, extversion 
            FROM pg_extension 
            ORDER BY extname
        """)
        extensions = cur.fetchall()
        
        # Verificar funções
        cur.execute("""
            SELECT routine_name 
            FROM information_schema.routines 
            WHERE routine_schema = 'public' 
            AND routine_type = 'FUNCTION'
            ORDER BY routine_name
        """)
        functions = cur.fetchall()
        
        conn.close()
        
        return True, {
            'tables': [t[0] for t in tables],
            'extensions': [(e[0], e[1]) for e in extensions],
            'functions': [f[0] for f in functions]
        }
    except Exception as e:
        return False, str(e)

def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print("Uso: python db_manager.py <comando>")
        print("Comandos disponíveis:")
        print("  status    - Verificar status das migrações")
        print("  migrate   - Executar migrações pendentes")
        print("  clean     - Limpar banco (apenas desenvolvimento)")
        print("  info      - Mostrar informações do schema")
        print("  check     - Verificar conexão com banco")
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        print("Verificando status das migrações...")
        success, output = get_migration_status()
        if success:
            print(output)
        else:
            print(f"Erro: {output}")
    
    elif command == "migrate":
        print("Executando migrações...")
        success, output = migrate_database()
        if success:
            print("Migrações executadas com sucesso!")
            print(output)
        else:
            print(f"Erro nas migrações: {output}")
    
    elif command == "clean":
        print("Limpando banco de dados...")
        success, output = clean_database()
        if success:
            print("Banco limpo com sucesso!")
            print(output)
        else:
            print(f"Erro ao limpar banco: {output}")
    
    elif command == "info":
        print("Obtendo informações do schema...")
        success, info = show_schema_info()
        if success:
            print("\n=== TABELAS ===")
            for table in info['tables']:
                print(f"  - {table}")
            
            print("\n=== EXTENSÕES ===")
            for ext, version in info['extensions']:
                print(f"  - {ext} (v{version})")
            
            print("\n=== FUNÇÕES ===")
            for func in info['functions']:
                print(f"  - {func}")
        else:
            print(f"Erro: {info}")
    
    elif command == "check":
        print("Verificando conexão com banco...")
        success, output = check_database_connection()
        if success:
            print("Conexão estabelecida com sucesso!")
            print(f"PostgreSQL: {output}")
        else:
            print(f"Erro na conexão: {output}")
    
    else:
        print(f"Comando desconhecido: {command}")

if __name__ == "__main__":
    main()
