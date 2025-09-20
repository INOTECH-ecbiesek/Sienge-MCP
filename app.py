#!/usr/bin/env python3
"""
Script de inicialização para Railway
"""

import os
from src.sienge_mcp.server import mcp

if __name__ == "__main__":
    # Railway define automaticamente a porta via variável PORT
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 Iniciando Sienge MCP Server na porta {port}")
    print(f"🌐 FastMCP Server rodando em: http://0.0.0.0:{port}")
    print(f"📚 Documentação disponível em: http://0.0.0.0:{port}/docs")
    
    # Rodar o servidor FastMCP usando o método run_server
    mcp.run_server(
        transport="http",
        host="0.0.0.0",
        port=port
    )