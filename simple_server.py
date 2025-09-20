#!/usr/bin/env python3
"""
Servidor MCP para Sienge via FastMCP - Deploy Railway sem healthcheck
"""

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    
    print(f"🚀 Sienge MCP Server via FastMCP HTTP")
    print(f"🌐 Rodando em: http://0.0.0.0:{port}")
    print(f"🔗 MCP Endpoint: http://0.0.0.0:{port}/mcp")
    print(f"🔧 Tools disponíveis via MCP para agentes")
    print(f"📚 20+ ferramentas Sienge integradas")
    
    try:
        # Executar o servidor MCP diretamente
        from src.sienge_mcp.server import mcp
        print("🎯 Iniciando FastMCP em modo HTTP...")
        mcp.run(transport="http", host="0.0.0.0", port=port)
    except Exception as ex:
        print(f"❌ Erro ao executar MCP: {ex}")
        print("🔄 Tentando fallback...")
        # Fallback para main()
        from src.sienge_mcp.server import main
        main()