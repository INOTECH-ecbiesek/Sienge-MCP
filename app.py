#!/usr/bin/env python3
"""
Script de inicialização para Railway
"""

import os
import subprocess
import sys

if __name__ == "__main__":
    # Railway define automaticamente a porta via variável PORT
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 Iniciando Sienge MCP Server na porta {port}")
    print(f"🌐 FastMCP Server rodando em: http://0.0.0.0:{port}")
    print(f"📚 Documentação disponível em: http://0.0.0.0:{port}/docs")
    
    # Usar o comando fastmcp diretamente
    cmd = [
        sys.executable, "-m", "fastmcp",
        "src.sienge_mcp.server:mcp",
        "--host", "0.0.0.0",
        "--port", str(port)
    ]
    
    subprocess.run(cmd)