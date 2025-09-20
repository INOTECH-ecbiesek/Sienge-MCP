#!/usr/bin/env python3
"""
Teste das funcionalidades MCP do servidor Sienge
"""

import asyncio
import aiohttp
import json

async def test_mcp_server():
    """Testa as funcionalidades do servidor MCP"""
    base_url = "https://sienge-mcp-production.up.railway.app/mcp"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Teste 1: Verificar se o servidor está respondendo
    print("🧪 Testando servidor MCP...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Teste básico de conectividade
            async with session.get(base_url) as response:
                print(f"✅ Servidor respondendo: {response.status}")
                
            # Teste de inicialização MCP
            init_data = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            async with session.post(base_url, json=init_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Inicialização MCP: {result.get('result', {}).get('serverInfo', {}).get('name', 'OK')}")
                else:
                    print(f"❌ Erro na inicialização: {response.status}")
            
            # Teste de listagem de tools
            tools_data = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
            
            async with session.post(base_url, json=tools_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    tools = result.get('result', {}).get('tools', [])
                    print(f"✅ Tools disponíveis: {len(tools)}")
                    
                    # Listar algumas tools de search
                    search_tools = [t for t in tools if 'search' in t.get('name', '').lower()]
                    if search_tools:
                        print("🔍 Tools de Search encontradas:")
                        for tool in search_tools[:3]:  # Primeiras 3
                            print(f"  - {tool.get('name')}: {tool.get('description', '')[:60]}...")
                    else:
                        print("❌ Nenhuma tool de search encontrada")
                else:
                    print(f"❌ Erro ao listar tools: {response.status}")
                    
        except Exception as e:
            print(f"❌ Erro na conexão: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())