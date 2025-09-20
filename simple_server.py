#!/usr/bin/env python3
"""
Servidor HTTP simples para o Sienge MCP
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from src.sienge_mcp.server import (
    test_sienge_connection,
    get_sienge_customers, 
    get_sienge_accounts_receivable,
    get_sienge_bills,
    get_sienge_purchase_orders,
    get_sienge_projects
)

app = FastAPI(
    title="Sienge MCP HTTP API",
    description="🏗️ API HTTP do Sienge MCP para Railway",
    version="1.1.5"
)

@app.get("/")
async def root():
    return {
        "message": "🏗️ Sienge MCP Server",
        "version": "1.1.5", 
        "status": "online",
        "endpoints": {
            "docs": "/docs",
            "test": "/test-connection",
            "customers": "/customers",
            "receivables": "/receivables",
            "bills": "/bills",
            "orders": "/purchase-orders",
            "projects": "/projects"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "sienge-mcp"}

@app.post("/test-connection")
async def api_test_connection():
    """Testa conexão com a API do Sienge"""
    try:
        result = await test_sienge_connection()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/customers") 
async def api_get_customers(limit: int = 50, offset: int = 0, search: str = None):
    """Busca clientes"""
    try:
        result = await get_sienge_customers(limit=limit, offset=offset, search=search)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/receivables")
async def api_get_receivables(start_date: str, end_date: str, selection_type: str = "D"):
    """Busca contas a receber"""
    try:
        result = await get_sienge_accounts_receivable(
            start_date=start_date, 
            end_date=end_date, 
            selection_type=selection_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bills")
async def api_get_bills(start_date: str = None, end_date: str = None, limit: int = 50):
    """Busca títulos a pagar"""
    try:
        result = await get_sienge_bills(
            start_date=start_date,
            end_date=end_date, 
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/purchase-orders")
async def api_get_purchase_orders(limit: int = 50):
    """Busca pedidos de compra"""
    try:
        result = await get_sienge_purchase_orders(limit=limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects")
async def api_get_projects(limit: int = 50):
    """Busca projetos/obras"""
    try:
        result = await get_sienge_projects(limit=limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 Sienge MCP HTTP Server")
    print(f"🌐 Rodando em: http://0.0.0.0:{port}")
    print(f"📚 Docs: http://0.0.0.0:{port}/docs") 
    print(f"✅ Health: http://0.0.0.0:{port}/health")
    
    uvicorn.run(app, host="0.0.0.0", port=port)