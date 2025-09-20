#!/usr/bin/env python3
"""
Script de inicialização para Railway - HTTP Server
"""

import os
import uvicorn
from fastapi import FastAPI
from src.sienge_mcp.server import mcp

# Criar app FastAPI
app = FastAPI(
    title="Sienge MCP Server",
    description="🏗️ Servidor HTTP do Sienge MCP para integração via Railway",
    version="1.1.5"
)

# Montar o servidor MCP como rotas HTTP
mcp.mount_fastapi(app)

if __name__ == "__main__":
    # Railway define automaticamente a porta via variável PORT
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 Iniciando Sienge MCP Server na porta {port}")
    print(f"🌐 HTTP Server rodando em: http://0.0.0.0:{port}")
    print(f"📚 Documentação disponível em: http://0.0.0.0:{port}/docs")
    print(f"🔧 Ferramentas MCP em: http://0.0.0.0:{port}/mcp/tools/")
    
    # Rodar servidor HTTP
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )