#!/usr/bin/env python3
"""
Script de inicialização para Railway
"""

import os
import uvicorn
from src.sienge_mcp.server import mcp

if __name__ == "__main__":
    # Railway define automaticamente a porta via variável PORT
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 Iniciando Sienge MCP Server na porta {port}")
    print(f"🌐 FastMCP Server rodando em: http://0.0.0.0:{port}")
    print(f"📚 Documentação disponível em: http://0.0.0.0:{port}/docs")
    
    # Usar uvicorn para rodar o servidor FastMCP como HTTP
    uvicorn.run(
        mcp.app,  # O app FastAPI do FastMCP
        host="0.0.0.0",
        port=port,
        log_level="info"
    )