#!/usr/bin/env python3
"""
SIENGE MCP COMPLETO - FastMCP com Autenticação Flexível
Suporta Bearer Token e Basic Auth
CORREÇÕES IMPLEMENTADAS:
1. Separação entre camada MCP e camada de serviços
2. Alias compatíveis com checklist
3. Normalização de parâmetros (camelCase + arrays)
4. Bulk-data assíncrono com polling
5. Observabilidade mínima (X-Request-ID, cache, logs)
6. Ajustes de compatibilidade pontuais
"""

from fastmcp import FastMCP
import httpx
from typing import Dict, List, Optional, Any, Union
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import uuid
import asyncio
import json
import time
import logging
from functools import wraps

# Carrega as variáveis de ambiente
load_dotenv()

mcp = FastMCP("Sienge API Integration 🏗️ - ChatGPT Compatible")

# Configurações da API do Sienge
SIENGE_BASE_URL = os.getenv("SIENGE_BASE_URL", "https://api.sienge.com.br")
SIENGE_SUBDOMAIN = os.getenv("SIENGE_SUBDOMAIN", "")
SIENGE_USERNAME = os.getenv("SIENGE_USERNAME", "")
SIENGE_PASSWORD = os.getenv("SIENGE_PASSWORD", "")
SIENGE_API_KEY = os.getenv("SIENGE_API_KEY", "")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

# Cache simples em memória
_cache = {}
CACHE_TTL = 300  # 5 minutos

# Configurar logging estruturado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sienge-mcp")


class SiengeAPIError(Exception):
    """Exceção customizada para erros da API do Sienge"""
    pass


# ============ HELPERS DE NORMALIZAÇÃO E OBSERVABILIDADE ============

def _camel(s: str) -> str:
    """Converte snake_case para camelCase"""
    if '_' not in s:
        return s
    parts = s.split('_')
    return parts[0] + ''.join(x.capitalize() for x in parts[1:])


def to_query(params: dict) -> dict:
    """
    Converte parâmetros para query string normalizada:
    - snake_case → camelCase
    - listas/tuplas → CSV string
    - booleanos → 'true'/'false' (minúsculo)
    - remove valores None
    """
    if not params:
        return {}
    
    out = {}
    for k, v in params.items():
        if v is None:
            continue
        key = _camel(k)
        if isinstance(v, (list, tuple)):
            out[key] = ','.join(map(str, v))
        elif isinstance(v, bool):
            out[key] = 'true' if v else 'false'
        else:
            out[key] = v
    return out


def to_camel_json(obj: Any) -> Any:
    """
    Normaliza payload JSON recursivamente:
    - snake_case → camelCase nas chaves
    - remove valores None
    - mantém estrutura de listas e objetos aninhados
    """
    if isinstance(obj, dict):
        return {_camel(k): to_camel_json(v) for k, v in obj.items() if v is not None}
    elif isinstance(obj, list):
        return [to_camel_json(x) for x in obj]
    else:
        return obj


def _normalize_url(base_url: str, subdomain: str) -> str:
    """Normaliza URL evitando //public/api quando subdomain está vazio"""
    if not subdomain or subdomain.strip() == "":
        return f"{base_url.rstrip('/')}/public/api"
    return f"{base_url.rstrip('/')}/{subdomain.strip()}/public/api"


def _parse_numeric_value(value: Any) -> float:
    """Sanitiza valores numéricos, lidando com vírgulas decimais"""
    if value is None:
        return 0.0
    
    if isinstance(value, (int, float)):
        return float(value)
    
    # Se for string, tentar converter
    str_value = str(value).strip()
    if not str_value:
        return 0.0
    
    # Trocar vírgula por ponto decimal
    str_value = str_value.replace(',', '.')
    
    try:
        return float(str_value)
    except (ValueError, TypeError):
        logger.warning(f"Não foi possível converter '{value}' para número")
        return 0.0


def _get_cache_key(endpoint: str, params: dict = None) -> str:
    """Gera chave de cache baseada no endpoint e parâmetros"""
    cache_params = json.dumps(params or {}, sort_keys=True)
    return f"{endpoint}:{hash(cache_params)}"


def _set_cache(key: str, data: Any) -> None:
    """Armazena dados no cache com TTL"""
    _cache[key] = {
        "data": data,
        "timestamp": time.time(),
        "ttl": CACHE_TTL
    }


def _get_cache(key: str) -> Optional[Dict]:
    """Recupera dados do cache se ainda válidos - CORRIGIDO: mantém shape original"""
    if key not in _cache:
        return None
    
    cached = _cache[key]
    if time.time() - cached["timestamp"] > cached["ttl"]:
        del _cache[key]  # Remove cache expirado
        return None
    
    # cached["data"] já é o "result" completo salvo em _set_cache
    result = dict(cached["data"])  # cópia rasa
    result["cache"] = {
        "hit": True,
        "ttl_s": cached["ttl"] - (time.time() - cached["timestamp"])
    }
    return result


def _log_request(method: str, endpoint: str, status_code: int, latency: float, request_id: str) -> None:
    """Log estruturado das requisições"""
    logger.info(
        f"HTTP {method} {endpoint} - Status: {status_code} - "
        f"Latency: {latency:.3f}s - RequestID: {request_id}"
    )


def _extract_items_and_total(resp_data: Any) -> tuple:
    """
    Extrai items e total count de resposta padronizada da API Sienge
    Retorna: (items_list, total_count)
    """
    items = resp_data.get("results", []) if isinstance(resp_data, dict) else (resp_data or [])
    meta = resp_data.get("resultSetMetadata", {}) if isinstance(resp_data, dict) else {}
    total = meta.get("count", len(items))
    return items, total


async def make_sienge_request(
    method: str, endpoint: str, params: Optional[Dict] = None, json_data: Optional[Dict] = None, use_cache: bool = True
) -> Dict:
    """
    Função auxiliar para fazer requisições à API do Sienge (v1)
    Suporta tanto Bearer Token quanto Basic Auth
    MELHORADO: Observabilidade, cache, normalização de parâmetros
    """
    start_time = time.time()
    req_id = str(uuid.uuid4())
    
    try:
        # Normalizar parâmetros
        normalized_params = to_query(params) if params else None
        
        # Verificar cache para operações GET
        cache_key = None
        if method.upper() == "GET" and use_cache and endpoint in ["/customer-types", "/creditors", "/customers"]:
            cache_key = _get_cache_key(endpoint, normalized_params)
            cached_result = _get_cache(cache_key)
            if cached_result:
                cached_result["request_id"] = req_id
                return cached_result
        
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            headers = {
                "Content-Type": "application/json", 
                "Accept": "application/json",
                "X-Request-ID": req_id
            }

            # Configurar autenticação e URL (corrigindo URLs duplas)
            auth = None
            base_normalized = _normalize_url(SIENGE_BASE_URL, SIENGE_SUBDOMAIN)

            if SIENGE_API_KEY and SIENGE_API_KEY != "sua_api_key_aqui":
                headers["Authorization"] = f"Bearer {SIENGE_API_KEY}"
                url = f"{base_normalized}/v1{endpoint}"
            elif SIENGE_USERNAME and SIENGE_PASSWORD:
                auth = httpx.BasicAuth(SIENGE_USERNAME, SIENGE_PASSWORD)
                url = f"{base_normalized}/v1{endpoint}"
            else:
                return {
                    "success": False,
                    "error": "No Authentication",
                    "message": "Configure SIENGE_API_KEY ou SIENGE_USERNAME/PASSWORD no .env",
                    "request_id": req_id
                }

            response = await client.request(
                method=method, 
                url=url, 
                headers=headers, 
                params=normalized_params, 
                json=json_data, 
                auth=auth
            )
            
            latency = time.time() - start_time
            _log_request(method, endpoint, response.status_code, latency, req_id)

            if response.status_code in [200, 201]:
                try:
                    data = response.json()
                    result = {
                        "success": True, 
                        "data": data, 
                        "status_code": response.status_code,
                        "request_id": req_id,
                        "latency_ms": round(latency * 1000, 2)
                    }
                    
                    # Armazenar no cache se aplicável
                    if cache_key and method.upper() == "GET":
                        _set_cache(cache_key, result)
                        result["cache"] = {"hit": False, "ttl_s": CACHE_TTL}
                    
                    return result
                    
                except Exception:
                    return {
                        "success": True, 
                        "data": {"message": "Success"}, 
                        "status_code": response.status_code,
                        "request_id": req_id,
                        "latency_ms": round(latency * 1000, 2)
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "message": response.text,
                    "status_code": response.status_code,
                    "request_id": req_id,
                    "latency_ms": round(latency * 1000, 2)
                }

    except httpx.TimeoutException:
        latency = time.time() - start_time
        _log_request(method, endpoint, 408, latency, req_id)
        return {
            "success": False, 
            "error": "Timeout", 
            "message": f"A requisição excedeu o tempo limite de {REQUEST_TIMEOUT}s",
            "request_id": req_id,
            "latency_ms": round(latency * 1000, 2)
        }
    except Exception as e:
        latency = time.time() - start_time
        _log_request(method, endpoint, 500, latency, req_id)
        return {
            "success": False, 
            "error": str(e), 
            "message": f"Erro na requisição: {str(e)}",
            "request_id": req_id,
            "latency_ms": round(latency * 1000, 2)
        }


async def make_sienge_bulk_request(
    method: str, endpoint: str, params: Optional[Dict] = None, json_data: Optional[Dict] = None
) -> Dict:
    """
    Função auxiliar para fazer requisições à API bulk-data do Sienge
    Suporta tanto Bearer Token quanto Basic Auth
    MELHORADO: Observabilidade e normalização de parâmetros
    """
    start_time = time.time()
    req_id = str(uuid.uuid4())
    
    try:
        # Normalizar parâmetros
        normalized_params = to_query(params) if params else None
        
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            headers = {
                "Content-Type": "application/json", 
                "Accept": "application/json",
                "X-Request-ID": req_id
            }

            # Configurar autenticação e URL para bulk-data (corrigindo URLs duplas)
            auth = None
            base_normalized = _normalize_url(SIENGE_BASE_URL, SIENGE_SUBDOMAIN)

            if SIENGE_API_KEY and SIENGE_API_KEY != "sua_api_key_aqui":
                headers["Authorization"] = f"Bearer {SIENGE_API_KEY}"
                url = f"{base_normalized}/bulk-data/v1{endpoint}"
            elif SIENGE_USERNAME and SIENGE_PASSWORD:
                auth = httpx.BasicAuth(SIENGE_USERNAME, SIENGE_PASSWORD)
                url = f"{base_normalized}/bulk-data/v1{endpoint}"
            else:
                return {
                    "success": False,
                    "error": "No Authentication",
                    "message": "Configure SIENGE_API_KEY ou SIENGE_USERNAME/PASSWORD no .env",
                    "request_id": req_id
                }

            response = await client.request(
                method=method, 
                url=url, 
                headers=headers, 
                params=normalized_params, 
                json=json_data, 
                auth=auth
            )
            
            latency = time.time() - start_time
            _log_request(method, f"bulk-data{endpoint}", response.status_code, latency, req_id)

            if response.status_code in [200, 201, 202]:
                try:
                    return {
                        "success": True, 
                        "data": response.json(), 
                        "status_code": response.status_code,
                        "request_id": req_id,
                        "latency_ms": round(latency * 1000, 2)
                    }
                except Exception:
                    return {
                        "success": True, 
                        "data": {"message": "Success"}, 
                        "status_code": response.status_code,
                        "request_id": req_id,
                        "latency_ms": round(latency * 1000, 2)
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "message": response.text,
                    "status_code": response.status_code,
                    "request_id": req_id,
                    "latency_ms": round(latency * 1000, 2)
                }

    except httpx.TimeoutException:
        latency = time.time() - start_time
        _log_request(method, f"bulk-data{endpoint}", 408, latency, req_id)
        return {
            "success": False, 
            "error": "Timeout", 
            "message": f"A requisição excedeu o tempo limite de {REQUEST_TIMEOUT}s",
            "request_id": req_id,
            "latency_ms": round(latency * 1000, 2)
        }
    except Exception as e:
        latency = time.time() - start_time
        _log_request(method, f"bulk-data{endpoint}", 500, latency, req_id)
        return {
            "success": False, 
            "error": str(e), 
            "message": f"Erro na requisição bulk-data: {str(e)}",
            "request_id": req_id,
            "latency_ms": round(latency * 1000, 2)
        }


async def _fetch_bulk_with_polling(method: str, endpoint: str, params: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Dict:
    """
    Faz requisição bulk com polling automático para requests assíncronos (202)
    """
    correlation_id = str(uuid.uuid4())
    
    # Fazer requisição inicial
    result = await make_sienge_bulk_request(method, endpoint, params, json_data)
    
    # Se não foi 202 ou não tem identifier, retornar resultado direto
    if result.get("status_code") != 202:
        return result
    
    data = result.get("data", {})
    if not isinstance(data, dict) or not data.get("identifier"):
        return result
    
    # Processar requisição assíncrona com polling
    identifier = data["identifier"]
    request_id = result.get("request_id")
    
    logger.info(f"Iniciando polling para bulk request - Identifier: {identifier} - RequestID: {request_id}")
    
    max_attempts = 30  # Máximo 5 minutos (30 * 10s)
    attempt = 0
    backoff_delay = 2  # Começar com 2 segundos
    
    while attempt < max_attempts:
        attempt += 1
        await asyncio.sleep(backoff_delay)
        
        # Verificar status do processamento
        status_result = await make_sienge_bulk_request("GET", f"/async/{identifier}")
        
        if not status_result["success"]:
            logger.error(f"Erro ao verificar status do bulk request {identifier}: {status_result.get('error')}")
            break
        
        status_data = status_result.get("data", {})
        status = status_data.get("status", "unknown")
        
        logger.info(f"Polling attempt {attempt} - Status: {status} - Identifier: {identifier}")
        
        if status == "completed":
            # Buscar resultados finais
            all_chunks = []
            chunk_count = status_data.get("chunk_count", 1)
            
            chunks_downloaded = 0
            for chunk_num in range(chunk_count):
                try:
                    # CORRIGIDO: endpoint aninhado sob /async
                    chunk_result = await make_sienge_bulk_request("GET", f"/async/{identifier}/result/{chunk_num}")
                    if chunk_result["success"]:
                        chunk_data = chunk_result.get("data", {}).get("data", [])
                        if isinstance(chunk_data, list):
                            all_chunks.extend(chunk_data)
                        chunks_downloaded += 1
                except Exception as e:
                    logger.warning(f"Erro ao buscar chunk {chunk_num}: {e}")
            
            return {
                "success": True,
                "data": all_chunks,
                "async_identifier": identifier,
                "correlation_id": correlation_id,
                "chunks_downloaded": chunks_downloaded,
                "rows_returned": len(all_chunks),
                "polling_attempts": attempt,
                "request_id": request_id
            }
        
        elif status == "failed" or status == "error":
            return {
                "success": False,
                "error": "Bulk processing failed",
                "message": status_data.get("error_message", "Processamento bulk falhou"),
                "async_identifier": identifier,
                "correlation_id": correlation_id,
                "polling_attempts": attempt,
                "request_id": request_id
            }
        
        # Aumentar delay progressivamente (backoff exponencial limitado)
        backoff_delay = min(backoff_delay * 1.5, 10)  # Máximo 10 segundos
    
    # Timeout do polling
    return {
        "success": False,
        "error": "Polling timeout",
        "message": f"Processamento bulk não completou em {max_attempts} tentativas",
        "async_identifier": identifier,
        "correlation_id": correlation_id,
        "polling_attempts": attempt,
        "request_id": request_id
    }


# ============ CAMADA DE SERVIÇOS (FUNÇÕES INTERNAS) ============

async def _svc_get_customer_types() -> Dict:
    """Serviço interno: buscar tipos de clientes"""
    return await make_sienge_request("GET", "/customer-types", use_cache=True)


async def _svc_get_customers(*, limit: int = 50, offset: int = 0, search: str = None, customer_type_id: str = None) -> Dict:
    """Serviço interno: buscar clientes"""
    params = {"limit": min(limit or 50, 200), "offset": offset or 0}
    if search:
        params["search"] = search
    if customer_type_id:
        params["customer_type_id"] = customer_type_id
    
    return await make_sienge_request("GET", "/customers", params=params)


async def _svc_get_creditors(*, limit: int = 50, offset: int = 0, search: str = None) -> Dict:
    """Serviço interno: buscar credores/fornecedores"""
    params = {"limit": min(limit or 50, 200), "offset": offset or 0}
    if search:
        params["search"] = search
    
    return await make_sienge_request("GET", "/creditors", params=params)


async def _svc_get_creditor_bank_info(*, creditor_id: str) -> Dict:
    """Serviço interno: informações bancárias de credor"""
    return await make_sienge_request("GET", f"/creditors/{creditor_id}/bank-informations")


async def _svc_get_projects(*, limit: int = 100, offset: int = 0, company_id: int = None, 
                           enterprise_type: int = None, receivable_register: str = None,
                           only_buildings_enabled: bool = False) -> Dict:
    """Serviço interno: buscar empreendimentos/projetos"""
    params = {"limit": min(limit or 100, 200), "offset": offset or 0}
    
    if company_id:
        params["company_id"] = company_id
    if enterprise_type:
        params["type"] = enterprise_type
    if receivable_register:
        params["receivable_register"] = receivable_register
    if only_buildings_enabled:
        params["only_buildings_enabled_for_integration"] = only_buildings_enabled
    
    return await make_sienge_request("GET", "/enterprises", params=params)


async def _svc_get_bills(*, start_date: str = None, end_date: str = None, creditor_id: str = None, 
                        status: str = None, limit: int = 50) -> Dict:
    """Serviço interno: buscar títulos a pagar"""
    # Se start_date não fornecido, usar últimos 30 dias
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # Se end_date não fornecido, usar hoje
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    params = {"start_date": start_date, "end_date": end_date, "limit": min(limit or 50, 200)}
    
    if creditor_id:
        params["creditor_id"] = creditor_id
    if status:
        params["status"] = status
    
    return await make_sienge_request("GET", "/bills", params=params)


async def _svc_get_accounts_receivable(*, start_date: str, end_date: str, selection_type: str = "D",
                                      company_id: int = None, cost_centers_id: List[int] = None,
                                      correction_indexer_id: int = None, correction_date: str = None,
                                      change_start_date: str = None, completed_bills: str = None,
                                      origins_ids: List[str] = None, bearers_id_in: List[int] = None,
                                      bearers_id_not_in: List[int] = None) -> Dict:
    """Serviço interno: buscar contas a receber via bulk-data"""
    params = {"start_date": start_date, "end_date": end_date, "selection_type": selection_type}
    
    if company_id:
        params["company_id"] = company_id
    if cost_centers_id:
        params["cost_centers_id"] = cost_centers_id
    if correction_indexer_id:
        params["correction_indexer_id"] = correction_indexer_id
    if correction_date:
        params["correction_date"] = correction_date
    if change_start_date:
        params["change_start_date"] = change_start_date
    if completed_bills:
        params["completed_bills"] = completed_bills
    if origins_ids:
        params["origins_ids"] = origins_ids
    if bearers_id_in:
        params["bearers_id_in"] = bearers_id_in
    if bearers_id_not_in:
        params["bearers_id_not_in"] = bearers_id_not_in
    
    return await _fetch_bulk_with_polling("GET", "/income", params=params)


async def _svc_get_accounts_receivable_by_bills(*, bills_ids: List[int], correction_indexer_id: int = None,
                                               correction_date: str = None) -> Dict:
    """Serviço interno: buscar contas a receber por títulos específicos"""
    params = {"bills_ids": bills_ids}
    
    if correction_indexer_id:
        params["correction_indexer_id"] = correction_indexer_id
    if correction_date:
        params["correction_date"] = correction_date
    
    return await _fetch_bulk_with_polling("GET", "/income/by-bills", params=params)


async def _svc_get_purchase_orders(*, purchase_order_id: str = None, status: str = None, 
                                  date_from: str = None, limit: int = 50) -> Dict:
    """Serviço interno: buscar pedidos de compra"""
    if purchase_order_id:
        return await make_sienge_request("GET", f"/purchase-orders/{purchase_order_id}")
    
    params = {"limit": min(limit or 50, 200)}
    if status:
        params["status"] = status
    if date_from:
        params["date_from"] = date_from
    
    return await make_sienge_request("GET", "/purchase-orders", params=params)


async def _svc_get_purchase_requests(*, purchase_request_id: str = None, limit: int = 50, status: str = None) -> Dict:
    """Serviço interno: buscar solicitações de compra"""
    if purchase_request_id:
        return await make_sienge_request("GET", f"/purchase-requests/{purchase_request_id}")
    
    params = {"limit": min(limit or 50, 200)}
    if status:
        params["status"] = status
    
    return await make_sienge_request("GET", "/purchase-requests", params=params)


async def _svc_get_purchase_invoices(*, limit: int = 50, date_from: str = None) -> Dict:
    """Serviço interno: listar notas fiscais de compra"""
    params = {"limit": min(limit or 50, 200)}
    if date_from:
        params["date_from"] = date_from
    
    return await make_sienge_request("GET", "/purchase-invoices", params=params)


# ============ CONEXÃO E TESTE ============


@mcp.tool
async def test_sienge_connection(_meta: Optional[Dict] = None) -> Dict:
    """Testa a conexão com a API do Sienge"""
    try:
        # Usar serviço interno
        result = await _svc_get_customer_types()

        if result["success"]:
            auth_method = "Bearer Token" if SIENGE_API_KEY else "Basic Auth"
            return {
                "success": True,
                "message": "✅ Conexão com API do Sienge estabelecida com sucesso!",
                "api_status": "Online",
                "auth_method": auth_method,
                "timestamp": datetime.now().isoformat(),
                "request_id": result.get("request_id"),
                "latency_ms": result.get("latency_ms"),
                "cache": result.get("cache")
            }
        else:
            return {
                "success": False,
                "message": "❌ Falha ao conectar com API do Sienge",
                "error": result.get("error"),
                "details": result.get("message"),
                "timestamp": datetime.now().isoformat(),
                "request_id": result.get("request_id")
            }
    except Exception as e:
        return {
            "success": False,
            "message": "❌ Erro ao testar conexão",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


# ============ CLIENTES ============


@mcp.tool
async def get_sienge_customers(
    limit: Optional[int] = 50, offset: Optional[int] = 0, search: Optional[str] = None, customer_type_id: Optional[str] = None,
    _meta: Optional[Dict] = None
) -> Dict:
    """
    Busca clientes no Sienge com filtros

    Args:
        limit: Máximo de registros (padrão: 50)
        offset: Pular registros (padrão: 0)
        search: Buscar por nome ou documento
        customer_type_id: Filtrar por tipo de cliente
    """
    # Usar serviço interno
    result = await _svc_get_customers(
        limit=limit or 50, 
        offset=offset or 0, 
        search=search, 
        customer_type_id=customer_type_id
    )

    if result["success"]:
        data = result["data"]
        customers = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
        total_count = metadata.get("count", len(customers))

        return {
            "success": True,
            "message": f"✅ Encontrados {len(customers)} clientes (total: {total_count})",
            "customers": customers,
            "count": len(customers),
            "total_count": total_count,
            "filters_applied": {
                "limit": limit, "offset": offset, "search": search, "customer_type_id": customer_type_id
            },
            "request_id": result.get("request_id"),
            "latency_ms": result.get("latency_ms"),
            "cache": result.get("cache")
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar clientes",
        "error": result.get("error"),
        "details": result.get("message"),
        "request_id": result.get("request_id")
    }


@mcp.tool
async def get_sienge_customer_types(_meta: Optional[Dict] = None) -> Dict:
    """Lista tipos de clientes disponíveis"""
    # Usar serviço interno
    result = await _svc_get_customer_types()

    if result["success"]:
        data = result["data"]
        customer_types = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
        total_count = metadata.get("count", len(customer_types))

        return {
            "success": True,
            "message": f"✅ Encontrados {len(customer_types)} tipos de clientes (total: {total_count})",
            "customer_types": customer_types,
            "count": len(customer_types),
            "total_count": total_count,
            "request_id": result.get("request_id"),
            "latency_ms": result.get("latency_ms"),
            "cache": result.get("cache")
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar tipos de clientes",
        "error": result.get("error"),
        "details": result.get("message"),
        "request_id": result.get("request_id")
    }


# ============ ALIAS COMPATÍVEIS COM CHECKLIST ============

@mcp.tool
async def get_sienge_enterprises(
    limit: int = 100, offset: int = 0, company_id: int = None, enterprise_type: int = None,
    _meta: Optional[Dict] = None) -> Dict:
    """
    ALIAS: get_sienge_projects → get_sienge_enterprises
    Busca empreendimentos/obras (compatibilidade com checklist)
    """
    return await get_sienge_projects(
        limit=limit, 
        offset=offset, 
        company_id=company_id, 
        enterprise_type=enterprise_type
    )


@mcp.tool
async def get_sienge_suppliers(
    limit: int = 50,
    offset: int = 0,
    search: str = None,
    _meta: Optional[Dict] = None) -> Dict:
    """
    ALIAS: get_sienge_creditors → get_sienge_suppliers
    Busca fornecedores (compatibilidade com checklist)
    """
    return await get_sienge_creditors(limit=limit, offset=offset, search=search)


@mcp.tool
async def search_sienge_finances(
    period_start: str,
    period_end: str,
    account_type: Optional[str] = None,
    cost_center: Optional[str] = None,   # ignorado por enquanto (não suportado na API atual)
    amount_filter: Optional[str] = None,
    customer_creditor: Optional[str] = None
) -> Dict:
    """
    ALIAS: search_sienge_financial_data → search_sienge_finances
    - account_type: receivable | payable | both
    - amount_filter: "100..500", ">=1000", "<=500", ">100", "<200", "=750"
    - customer_creditor: termo de busca (cliente/credor)
    """
    # 1) mapear tipo
    search_type = (account_type or "both").lower()
    if search_type not in {"receivable", "payable", "both"}:
        search_type = "both"

    # 2) parse de faixa de valores
    amount_min = amount_max = None
    if amount_filter:
        s = amount_filter.replace(" ", "")
        try:
            if ".." in s:
                lo, hi = s.split("..", 1)
                amount_min = float(lo) if lo else None
                amount_max = float(hi) if hi else None
            elif s.startswith(">="):
                amount_min = float(s[2:])
            elif s.startswith("<="):
                amount_max = float(s[2:])
            elif s.startswith(">"):
                # >x  → min = x (estrito não suportado; aproximamos)
                amount_min = float(s[1:])
            elif s.startswith("<"):
                amount_max = float(s[1:])
            elif s.startswith("="):
                v = float(s[1:])
                amount_min = v
                amount_max = v
            else:
                # número puro → min
                amount_min = float(s)
        except ValueError:
            # filtro inválido → ignora silenciosamente
            amount_min = amount_max = None

    return await search_sienge_financial_data(
        period_start=period_start,
        period_end=period_end,
        search_type=search_type,
        amount_min=amount_min,
        amount_max=amount_max,
        customer_creditor_search=customer_creditor
    )


@mcp.tool
async def get_sienge_accounts_payable(
    start_date: str = None, end_date: str = None, creditor_id: str = None, 
    status: str = None, limit: int = 50,
    _meta: Optional[Dict] = None) -> Dict:
    """
    ALIAS: get_sienge_bills → get_sienge_accounts_payable
    Busca contas a pagar (compatibilidade com checklist)
    """
    return await get_sienge_bills(
        start_date=start_date,
        end_date=end_date,
        creditor_id=creditor_id,
        status=status,
        limit=limit
    )


@mcp.tool
async def list_sienge_purchase_invoices(limit: int = 50, date_from: str = None,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Lista notas fiscais de compra (versão list/plural esperada pelo checklist)
    
    Args:
        limit: Máximo de registros (padrão: 50, máx: 200)
        date_from: Data inicial (YYYY-MM-DD)
    """
    # Usar serviço interno
    result = await _svc_get_purchase_invoices(limit=limit, date_from=date_from)
    
    if result["success"]:
        data = result["data"]
        invoices = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
        total_count = metadata.get("count", len(invoices))

        return {
            "success": True,
            "message": f"✅ Encontradas {len(invoices)} notas fiscais de compra (total: {total_count})",
            "purchase_invoices": invoices,
            "count": len(invoices),
            "total_count": total_count,
            "filters_applied": {"limit": limit, "date_from": date_from},
            "request_id": result.get("request_id"),
            "latency_ms": result.get("latency_ms"),
            "cache": result.get("cache")
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar notas fiscais de compra",
        "error": result.get("error"),
        "details": result.get("message"),
        "request_id": result.get("request_id")
    }


@mcp.tool
async def list_sienge_purchase_requests(limit: int = 50, status: str = None,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Lista solicitações de compra (versão list/plural esperada pelo checklist)
    
    Args:
        limit: Máximo de registros (padrão: 50, máx: 200)
        status: Status da solicitação
    """
    # Usar serviço interno
    result = await _svc_get_purchase_requests(limit=limit, status=status)
    
    if result["success"]:
        data = result["data"]
        requests = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
        total_count = metadata.get("count", len(requests))

        return {
            "success": True,
            "message": f"✅ Encontradas {len(requests)} solicitações de compra (total: {total_count})",
            "purchase_requests": requests,
            "count": len(requests),
            "total_count": total_count,
            "filters_applied": {"limit": limit, "status": status},
            "request_id": result.get("request_id"),
            "latency_ms": result.get("latency_ms"),
            "cache": result.get("cache")
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar solicitações de compra",
        "error": result.get("error"),
        "details": result.get("message"),
        "request_id": result.get("request_id")
    }


# ============ CREDORES ============


@mcp.tool
async def get_sienge_creditors(limit: Optional[int] = 50, offset: Optional[int] = 0, search: Optional[str] = None,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Busca credores/fornecedores

    Args:
        limit: Máximo de registros (padrão: 50)
        offset: Pular registros (padrão: 0)
        search: Buscar por nome
    """
    # Usar serviço interno
    result = await _svc_get_creditors(
        limit=limit or 50,
        offset=offset or 0,
        search=search
    )

    if result["success"]:
        data = result["data"]
        creditors = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
        total_count = metadata.get("count", len(creditors))

        return {
            "success": True,
            "message": f"✅ Encontrados {len(creditors)} credores (total: {total_count})",
            "creditors": creditors,
            "count": len(creditors),
            "total_count": total_count,
            "filters_applied": {"limit": limit, "offset": offset, "search": search},
            "request_id": result.get("request_id"),
            "latency_ms": result.get("latency_ms"),
            "cache": result.get("cache")
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar credores",
        "error": result.get("error"),
        "details": result.get("message"),
        "request_id": result.get("request_id")
    }


@mcp.tool
async def get_sienge_creditor_bank_info(creditor_id: str,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Consulta informações bancárias de um credor

    Args:
        creditor_id: ID do credor (obrigatório)
    """
    # Usar serviço interno
    result = await _svc_get_creditor_bank_info(creditor_id=creditor_id)

    if result["success"]:
        return {
            "success": True,
            "message": f"✅ Informações bancárias do credor {creditor_id}",
            "creditor_id": creditor_id,
            "bank_info": result["data"],
            "request_id": result.get("request_id"),
            "latency_ms": result.get("latency_ms")
        }

    return {
        "success": False,
        "message": f"❌ Erro ao buscar info bancária do credor {creditor_id}",
        "error": result.get("error"),
        "details": result.get("message"),
        "request_id": result.get("request_id")
    }


# ============ FINANCEIRO ============


@mcp.tool
async def get_sienge_accounts_receivable(
    start_date: str,
    end_date: str,
    selection_type: str = "D",
    company_id: Optional[int] = None,
    cost_centers_id: Optional[List[int]] = None,
    correction_indexer_id: Optional[int] = None,
    correction_date: Optional[str] = None,
    change_start_date: Optional[str] = None,
    completed_bills: Optional[str] = None,
    origins_ids: Optional[List[str]] = None,
    bearers_id_in: Optional[List[int]] = None,
    bearers_id_not_in: Optional[List[int]] = None,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Consulta parcelas do contas a receber via API bulk-data
    MELHORADO: Suporte a polling assíncrono para requests 202

    Args:
        start_date: Data de início do período (YYYY-MM-DD) - OBRIGATÓRIO
        end_date: Data do fim do período (YYYY-MM-DD) - OBRIGATÓRIO
        selection_type: Seleção da data do período (I=emissão, D=vencimento, P=pagamento, B=competência) - padrão: D
        company_id: Código da empresa
        cost_centers_id: Lista de códigos de centro de custo
        correction_indexer_id: Código do indexador de correção
        correction_date: Data para correção do indexador (YYYY-MM-DD)
        change_start_date: Data inicial de alteração do título/parcela (YYYY-MM-DD)
        completed_bills: Filtrar por títulos completos (S)
        origins_ids: Códigos dos módulos de origem (CR, CO, ME, CA, CI, AR, SC, LO, NE, NS, AC, NF)
        bearers_id_in: Filtrar parcelas com códigos de portador específicos
        bearers_id_not_in: Filtrar parcelas excluindo códigos de portador específicos
    """
    # Usar serviço interno com polling assíncrono
    result = await _svc_get_accounts_receivable(
        start_date=start_date,
        end_date=end_date,
        selection_type=selection_type,
        company_id=company_id,
        cost_centers_id=cost_centers_id,
        correction_indexer_id=correction_indexer_id,
        correction_date=correction_date,
        change_start_date=change_start_date,
        completed_bills=completed_bills,
        origins_ids=origins_ids,
        bearers_id_in=bearers_id_in,
        bearers_id_not_in=bearers_id_not_in
    )

    if result["success"]:
        # Para requests normais (200) e assíncronos processados
        income_data = result.get("data", [])
        
        response = {
            "success": True,
            "message": f"✅ Encontradas {len(income_data)} parcelas a receber",
            "income_data": income_data,
            "count": len(income_data),
            "period": f"{start_date} a {end_date}",
            "selection_type": selection_type,
            "request_id": result.get("request_id"),
            "latency_ms": result.get("latency_ms")
        }
        
        # Se foi processamento assíncrono, incluir informações extras
        if result.get("async_identifier"):
            response.update({
                "async_processing": {
                    "identifier": result.get("async_identifier"),
                    "correlation_id": result.get("correlation_id"),
                    "chunks_downloaded": result.get("chunks_downloaded"),
                    "rows_returned": result.get("rows_returned"),
                    "polling_attempts": result.get("polling_attempts")
                }
            })
        
        return response

    return {
        "success": False,
        "message": "❌ Erro ao buscar parcelas a receber",
        "error": result.get("error"),
        "details": result.get("message"),
        "request_id": result.get("request_id"),
        "async_info": {
            "identifier": result.get("async_identifier"),
            "polling_attempts": result.get("polling_attempts")
        } if result.get("async_identifier") else None
    }


@mcp.tool
async def get_sienge_accounts_receivable_by_bills(
    bills_ids: List[int], correction_indexer_id: Optional[int] = None, correction_date: Optional[str] = None,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Consulta parcelas dos títulos informados via API bulk-data
    MELHORADO: Suporte a polling assíncrono para requests 202

    Args:
        bills_ids: Lista de códigos dos títulos - OBRIGATÓRIO
        correction_indexer_id: Código do indexador de correção
        correction_date: Data para correção do indexador (YYYY-MM-DD)
    """
    # Usar serviço interno com polling assíncrono
    result = await _svc_get_accounts_receivable_by_bills(
        bills_ids=bills_ids,
        correction_indexer_id=correction_indexer_id,
        correction_date=correction_date
    )

    if result["success"]:
        income_data = result.get("data", [])
        
        response = {
            "success": True,
            "message": f"✅ Encontradas {len(income_data)} parcelas dos títulos informados",
            "income_data": income_data,
            "count": len(income_data),
            "bills_consulted": bills_ids,
            "request_id": result.get("request_id"),
            "latency_ms": result.get("latency_ms")
        }
        
        # Se foi processamento assíncrono, incluir informações extras
        if result.get("async_identifier"):
            response.update({
                "async_processing": {
                    "identifier": result.get("async_identifier"),
                    "correlation_id": result.get("correlation_id"),
                    "chunks_downloaded": result.get("chunks_downloaded"),
                    "rows_returned": result.get("rows_returned"),
                    "polling_attempts": result.get("polling_attempts")
                }
            })
        
        return response

    return {
        "success": False,
        "message": "❌ Erro ao buscar parcelas dos títulos informados",
        "error": result.get("error"),
        "details": result.get("message"),
        "request_id": result.get("request_id"),
        "async_info": {
            "identifier": result.get("async_identifier"),
            "polling_attempts": result.get("polling_attempts")
        } if result.get("async_identifier") else None
    }


@mcp.tool
async def get_sienge_bills(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    creditor_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: Optional[int] = 50,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Consulta títulos a pagar (contas a pagar) - REQUER startDate obrigatório

    Args:
        start_date: Data inicial obrigatória (YYYY-MM-DD) - padrão últimos 30 dias
        end_date: Data final (YYYY-MM-DD) - padrão hoje
        creditor_id: ID do credor
        status: Status do título (ex: open, paid, cancelled)
        limit: Máximo de registros (padrão: 50, máx: 200)
    """
    # Usar serviço interno
    result = await _svc_get_bills(
        start_date=start_date,
        end_date=end_date,
        creditor_id=creditor_id,
        status=status,
        limit=limit or 50
    )

    if result["success"]:
        data = result["data"]
        bills = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
        total_count = metadata.get("count", len(bills))

        # Aplicar parsing numérico nos valores
        for bill in bills:
            if "amount" in bill:
                bill["amount"] = _parse_numeric_value(bill["amount"])
            if "paid_amount" in bill:
                bill["paid_amount"] = _parse_numeric_value(bill["paid_amount"])
            if "remaining_amount" in bill:
                bill["remaining_amount"] = _parse_numeric_value(bill["remaining_amount"])

        # Usar datas padrão se não fornecidas
        actual_start = start_date or (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        actual_end = end_date or datetime.now().strftime("%Y-%m-%d")

        return {
            "success": True,
            "message": f"✅ Encontrados {len(bills)} títulos a pagar (total: {total_count}) - período: {actual_start} a {actual_end}",
            "bills": bills,
            "count": len(bills),
            "total_count": total_count,
            "period": {"start_date": actual_start, "end_date": actual_end},
            "filters_applied": {
                "start_date": actual_start, "end_date": actual_end, 
                "creditor_id": creditor_id, "status": status, "limit": limit
            },
            "request_id": result.get("request_id"),
            "latency_ms": result.get("latency_ms"),
            "cache": result.get("cache")
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar títulos a pagar",
        "error": result.get("error"),
        "details": result.get("message"),
        "request_id": result.get("request_id")
    }


# ============ COMPRAS ============


@mcp.tool
async def get_sienge_purchase_orders(
    purchase_order_id: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    limit: Optional[int] = 50,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Consulta pedidos de compra

    Args:
        purchase_order_id: ID específico do pedido
        status: Status do pedido
        date_from: Data inicial (YYYY-MM-DD)
        limit: Máximo de registros
    """
    if purchase_order_id:
        result = await make_sienge_request("GET", f"/purchase-orders/{purchase_order_id}")
        if result["success"]:
            return {"success": True, "message": f"✅ Pedido {purchase_order_id} encontrado", "purchase_order": result["data"]}
        return result

    params = {"limit": min(limit or 50, 200)}
    if status:
        params["status"] = status
    if date_from:
        params["date_from"] = date_from

    result = await make_sienge_request("GET", "/purchase-orders", params=params)

    if result["success"]:
        data = result["data"]
        orders = data.get("results", []) if isinstance(data, dict) else data

        return {
            "success": True,
            "message": f"✅ Encontrados {len(orders)} pedidos de compra",
            "purchase_orders": orders,
            "count": len(orders),
            "request_id": result.get("request_id"),
            "latency_ms": result.get("latency_ms")
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar pedidos de compra",
        "error": result.get("error"),
        "details": result.get("message"),
        "request_id": result.get("request_id"),
        "latency_ms": result.get("latency_ms")
    }


@mcp.tool
async def get_sienge_purchase_order_items(purchase_order_id: str,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Consulta itens de um pedido de compra específico

    Args:
        purchase_order_id: ID do pedido (obrigatório)
    """
    result = await make_sienge_request("GET", f"/purchase-orders/{purchase_order_id}/items")

    if result["success"]:
        data = result["data"]
        items = data.get("results", []) if isinstance(data, dict) else data

        return {
            "success": True,
            "message": f"✅ Encontrados {len(items)} itens no pedido {purchase_order_id}",
            "purchase_order_id": purchase_order_id,
            "items": items,
            "count": len(items),
        }

    return {
        "success": False,
        "message": f"❌ Erro ao buscar itens do pedido {purchase_order_id}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


@mcp.tool
async def get_sienge_purchase_requests(purchase_request_id: Optional[str] = None, limit: Optional[int] = 50,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Consulta solicitações de compra

    Args:
        purchase_request_id: ID específico da solicitação
        limit: Máximo de registros
    """
    if purchase_request_id:
        result = await make_sienge_request("GET", f"/purchase-requests/{purchase_request_id}")
        if result["success"]:
            return {
                "success": True,
                "message": f"✅ Solicitação {purchase_request_id} encontrada",
                "purchase_request": result["data"],
            }
        return result

    params = {"limit": min(limit or 50, 200)}
    result = await make_sienge_request("GET", "/purchase-requests", params=params)

    if result["success"]:
        data = result["data"]
        requests = data.get("results", []) if isinstance(data, dict) else data

        return {
            "success": True,
            "message": f"✅ Encontradas {len(requests)} solicitações de compra",
            "purchase_requests": requests,
            "count": len(requests),
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar solicitações de compra",
        "error": result.get("error"),
        "details": result.get("message"),
    }


@mcp.tool
async def create_sienge_purchase_request(description: str, project_id: str, items: List[Dict[str, Any]],
    _meta: Optional[Dict] = None) -> Dict:
    """
    Cria nova solicitação de compra

    Args:
        description: Descrição da solicitação
        project_id: ID do projeto/obra
        items: Lista de itens da solicitação
    """
    request_data = {
        "description": description,
        "project_id": project_id,
        "items": items,
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    # CORRIGIDO: Normalizar JSON payload
    json_data = to_camel_json(request_data)
    result = await make_sienge_request("POST", "/purchase-requests", json_data=json_data)

    if result["success"]:
        return {
            "success": True,
            "message": "✅ Solicitação de compra criada com sucesso",
            "request_id": result.get("request_id"),
            "purchase_request_id": result["data"].get("id"),
            "data": result["data"],
            "latency_ms": result.get("latency_ms")
        }

    return {
        "success": False,
        "message": "❌ Erro ao criar solicitação de compra",
        "error": result.get("error"),
        "details": result.get("message"),
        "request_id": result.get("request_id")
    }


# ============ NOTAS FISCAIS DE COMPRA ============


@mcp.tool
async def get_sienge_purchase_invoice(sequential_number: int,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Consulta nota fiscal de compra por número sequencial

    Args:
        sequential_number: Número sequencial da nota fiscal
    """
    result = await make_sienge_request("GET", f"/purchase-invoices/{sequential_number}")

    if result["success"]:
        return {"success": True, "message": f"✅ Nota fiscal {sequential_number} encontrada", "invoice": result["data"]}

    return {
        "success": False,
        "message": f"❌ Erro ao buscar nota fiscal {sequential_number}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


@mcp.tool
async def get_sienge_purchase_invoice_items(sequential_number: int,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Consulta itens de uma nota fiscal de compra

    Args:
        sequential_number: Número sequencial da nota fiscal
    """
    result = await make_sienge_request("GET", f"/purchase-invoices/{sequential_number}/items")

    if result["success"]:
        data = result["data"]
        items = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}

        return {
            "success": True,
            "message": f"✅ Encontrados {len(items)} itens na nota fiscal {sequential_number}",
            "items": items,
            "count": len(items),
            "metadata": metadata,
        }

    return {
        "success": False,
        "message": f"❌ Erro ao buscar itens da nota fiscal {sequential_number}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


@mcp.tool
async def create_sienge_purchase_invoice(
    document_id: str,
    number: str,
    supplier_id: int,
    company_id: int,
    movement_type_id: int,
    movement_date: str,
    issue_date: str,
    series: Optional[str] = None,
    notes: Optional[str] = None,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Cadastra uma nova nota fiscal de compra

    Args:
        document_id: ID do documento (ex: "NF")
        number: Número da nota fiscal
        supplier_id: ID do fornecedor
        company_id: ID da empresa
        movement_type_id: ID do tipo de movimento
        movement_date: Data do movimento (YYYY-MM-DD)
        issue_date: Data de emissão (YYYY-MM-DD)
        series: Série da nota fiscal (opcional)
        notes: Observações (opcional)
    """
    invoice_data = {
        "document_id": document_id,
        "number": number,
        "supplier_id": supplier_id,
        "company_id": company_id,
        "movement_type_id": movement_type_id,
        "movement_date": movement_date,
        "issue_date": issue_date,
    }

    if series:
        invoice_data["series"] = series
    if notes:
        invoice_data["notes"] = notes

    result = await make_sienge_request("POST", "/purchase-invoices", json_data=to_camel_json(invoice_data))

    if result["success"]:
        return {"success": True, "message": f"✅ Nota fiscal {number} criada com sucesso", "invoice": result["data"]}

    return {
        "success": False,
        "message": f"❌ Erro ao criar nota fiscal {number}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


@mcp.tool
async def add_items_to_purchase_invoice(
    sequential_number: int,
    deliveries_order: List[Dict[str, Any]],
    copy_notes_purchase_orders: bool = True,
    copy_notes_resources: bool = False,
    copy_attachments_purchase_orders: bool = True,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Insere itens em uma nota fiscal a partir de entregas de pedidos de compra

    Args:
        sequential_number: Número sequencial da nota fiscal
        deliveries_order: Lista de entregas com estrutura:
            - purchaseOrderId: ID do pedido de compra
            - itemNumber: Número do item no pedido
            - deliveryScheduleNumber: Número da programação de entrega
            - deliveredQuantity: Quantidade entregue
            - keepBalance: Manter saldo (true/false)
        copy_notes_purchase_orders: Copiar observações dos pedidos de compra
        copy_notes_resources: Copiar observações dos recursos
        copy_attachments_purchase_orders: Copiar anexos dos pedidos de compra
    """
    item_data = {
        "deliveries_order": deliveries_order,
        "copy_notes_purchase_orders": copy_notes_purchase_orders,
        "copy_notes_resources": copy_notes_resources,
        "copy_attachments_purchase_orders": copy_attachments_purchase_orders,
    }

    result = await make_sienge_request(
        "POST", f"/purchase-invoices/{sequential_number}/items/purchase-orders/delivery-schedules", json_data=to_camel_json(item_data)
    )

    if result["success"]:
        return {
            "success": True,
            "message": f"✅ Itens adicionados à nota fiscal {sequential_number} com sucesso",
            "item": result["data"],
        }

    return {
        "success": False,
        "message": f"❌ Erro ao adicionar itens à nota fiscal {sequential_number}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


@mcp.tool
async def get_sienge_purchase_invoices_deliveries_attended(
    bill_id: Optional[int] = None,
    sequential_number: Optional[int] = None,
    purchase_order_id: Optional[int] = None,
    invoice_item_number: Optional[int] = None,
    purchase_order_item_number: Optional[int] = None,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Lista entregas atendidas entre pedidos de compra e notas fiscais

    Args:
        bill_id: ID do título da nota fiscal
        sequential_number: Número sequencial da nota fiscal
        purchase_order_id: ID do pedido de compra
        invoice_item_number: Número do item da nota fiscal
        purchase_order_item_number: Número do item do pedido de compra
        limit: Máximo de registros (padrão: 100, máximo: 200)
        offset: Deslocamento (padrão: 0)
    """
    params = {"limit": min(limit or 100, 200), "offset": offset or 0}

    if bill_id:
        params["billId"] = bill_id
    if sequential_number:
        params["sequentialNumber"] = sequential_number
    if purchase_order_id:
        params["purchaseOrderId"] = purchase_order_id
    if invoice_item_number:
        params["invoiceItemNumber"] = invoice_item_number
    if purchase_order_item_number:
        params["purchaseOrderItemNumber"] = purchase_order_item_number

    result = await make_sienge_request("GET", "/purchase-invoices/deliveries-attended", params=params)

    if result["success"]:
        data = result["data"]
        deliveries = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}

        return {
            "success": True,
            "message": f"✅ Encontradas {len(deliveries)} entregas atendidas",
            "deliveries": deliveries,
            "count": len(deliveries),
            "metadata": metadata,
            "filters": params,
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar entregas atendidas",
        "error": result.get("error"),
        "details": result.get("message"),
    }


# ============ ESTOQUE ============


@mcp.tool
async def get_sienge_stock_inventory(cost_center_id: str, resource_id: Optional[str] = None,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Consulta inventário de estoque por centro de custo

    Args:
        cost_center_id: ID do centro de custo (obrigatório)
        resource_id: ID do insumo específico (opcional)
    """
    if resource_id:
        endpoint = f"/stock-inventories/{cost_center_id}/items/{resource_id}"
    else:
        endpoint = f"/stock-inventories/{cost_center_id}/items"

    result = await make_sienge_request("GET", endpoint)

    if result["success"]:
        data = result["data"]
        items = data.get("results", []) if isinstance(data, dict) else data
        count = len(items) if isinstance(items, list) else 1

        return {
            "success": True,
            "message": f"✅ Inventário do centro de custo {cost_center_id}",
            "cost_center_id": cost_center_id,
            "inventory": items,
            "count": count,
        }

    return {
        "success": False,
        "message": f"❌ Erro ao consultar estoque do centro {cost_center_id}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


@mcp.tool
async def get_sienge_stock_reservations(limit: Optional[int] = 50,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Lista reservas de estoque

    Args:
        limit: Máximo de registros
    """
    params = {"limit": min(limit or 50, 200)}
    result = await make_sienge_request("GET", "/stock-reservations", params=params)

    if result["success"]:
        data = result["data"]
        reservations = data.get("results", []) if isinstance(data, dict) else data

        return {
            "success": True,
            "message": f"✅ Encontradas {len(reservations)} reservas de estoque",
            "reservations": reservations,
            "count": len(reservations),
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar reservas de estoque",
        "error": result.get("error"),
        "details": result.get("message"),
    }


# ============ PROJETOS/OBRAS ============


@mcp.tool
async def get_sienge_projects(
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    company_id: Optional[int] = None,
    enterprise_type: Optional[int] = None,
    receivable_register: Optional[str] = None,
    only_buildings_enabled: Optional[bool] = False,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Busca empreendimentos/obras no Sienge
    CORRIGIDO: Mapeamento correto da chave de resposta

    Args:
        limit: Máximo de registros (padrão: 100, máximo: 200)
        offset: Pular registros (padrão: 0)
        company_id: Código da empresa
        enterprise_type: Tipo do empreendimento (1: Obra e Centro de custo, 2: Obra, 3: Centro de custo, 4: Centro de custo associado a obra)
        receivable_register: Filtro de registro de recebíveis (B3, CERC)
        only_buildings_enabled: Retornar apenas obras habilitadas para integração orçamentária
    """
    # Usar serviço interno
    result = await _svc_get_projects(
        limit=limit or 100,
        offset=offset or 0,
        company_id=company_id,
        enterprise_type=enterprise_type,
        receivable_register=receivable_register,
        only_buildings_enabled=only_buildings_enabled or False
    )

    if result["success"]:
        data = result["data"]
        # CORREÇÃO: API retorna em "results", mas paginador espera em "enterprises"
        enterprises = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
        total_count = metadata.get("count", len(enterprises))

        return {
            "success": True,
            "message": f"✅ Encontrados {len(enterprises)} empreendimentos (total: {total_count})",
            "enterprises": enterprises,  # Manter consistência para paginador
            "projects": enterprises,     # Alias para compatibilidade
            "count": len(enterprises),
            "total_count": total_count,
            "metadata": metadata,
            "filters_applied": {
                "limit": limit, "offset": offset, "company_id": company_id,
                "enterprise_type": enterprise_type, "receivable_register": receivable_register,
                "only_buildings_enabled": only_buildings_enabled
            },
            "request_id": result.get("request_id"),
            "latency_ms": result.get("latency_ms"),
            "cache": result.get("cache")
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar empreendimentos",
        "error": result.get("error"),
        "details": result.get("message"),
        "request_id": result.get("request_id")
    }


@mcp.tool
async def get_sienge_enterprise_by_id(enterprise_id: int,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Busca um empreendimento específico por ID no Sienge

    Args:
        enterprise_id: ID do empreendimento
    """
    result = await make_sienge_request("GET", f"/enterprises/{enterprise_id}")

    if result["success"]:
        return {"success": True, "message": f"✅ Empreendimento {enterprise_id} encontrado", "enterprise": result["data"]}

    return {
        "success": False,
        "message": f"❌ Erro ao buscar empreendimento {enterprise_id}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


@mcp.tool
async def get_sienge_enterprise_groupings(enterprise_id: int,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Busca agrupamentos de unidades de um empreendimento específico

    Args:
        enterprise_id: ID do empreendimento
    """
    result = await make_sienge_request("GET", f"/enterprises/{enterprise_id}/groupings")

    if result["success"]:
        groupings = result["data"]
        return {
            "success": True,
            "message": f"✅ Agrupamentos do empreendimento {enterprise_id} encontrados",
            "groupings": groupings,
            "count": len(groupings) if isinstance(groupings, list) else 0,
        }

    return {
        "success": False,
        "message": f"❌ Erro ao buscar agrupamentos do empreendimento {enterprise_id}",
        "error": result.get("error"),
        "details": result.get("message"),
    }


@mcp.tool
async def get_sienge_units(limit: Optional[int] = 50, offset: Optional[int] = 0,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Consulta unidades cadastradas no Sienge

    Args:
        limit: Máximo de registros (padrão: 50)
        offset: Pular registros (padrão: 0)
    """
    params = {"limit": min(limit or 50, 200), "offset": offset or 0}
    result = await make_sienge_request("GET", "/units", params=params)

    if result["success"]:
        data = result["data"]
        units = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
        total_count = metadata.get("count", len(units))

        return {
            "success": True,
            "message": f"✅ Encontradas {len(units)} unidades (total: {total_count})",
            "units": units,
            "count": len(units),
            "total_count": total_count,
            "request_id": result.get("request_id"),
            "latency_ms": result.get("latency_ms")
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar unidades",
        "error": result.get("error"),
        "details": result.get("message"),
        "request_id": result.get("request_id"),
        "latency_ms": result.get("latency_ms")
    }


# ============ CUSTOS ============


@mcp.tool
async def get_sienge_unit_cost_tables(
    table_code: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = "Active",
    integration_enabled: Optional[bool] = None,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Consulta tabelas de custos unitários

    Args:
        table_code: Código da tabela (opcional)
        description: Descrição da tabela (opcional)
        status: Status (Active/Inactive)
        integration_enabled: Se habilitada para integração
    """
    params = {"status": status or "Active"}

    if table_code:
        params["table_code"] = table_code
    if description:
        params["description"] = description
    if integration_enabled is not None:
        params["integration_enabled"] = integration_enabled

    result = await make_sienge_request("GET", "/unit-cost-tables", params=params)

    if result["success"]:
        data = result["data"]
        tables = data.get("results", []) if isinstance(data, dict) else data

        return {
            "success": True,
            "message": f"✅ Encontradas {len(tables)} tabelas de custos",
            "cost_tables": tables,
            "count": len(tables),
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar tabelas de custos",
        "error": result.get("error"),
        "details": result.get("message"),
    }


# ============ SEARCH UNIVERSAL (COMPATIBILIDADE CHATGPT) ============


@mcp.tool
async def search_sienge_data(
    query: str,
    entity_type: Optional[str] = None,
    limit: Optional[int] = 20,
    filters: Optional[Dict[str, Any]] = None,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Busca universal no Sienge - compatível com ChatGPT/OpenAI MCP
    
    Permite buscar em múltiplas entidades do Sienge de forma unificada.
    
    Args:
        query: Termo de busca (nome, código, descrição, etc.)
        entity_type: Tipo de entidade (customers, creditors, projects, bills, purchase_orders, etc.)
        limit: Máximo de registros (padrão: 20, máximo: 100)
        filters: Filtros específicos por tipo de entidade
    """
    search_results = []
    limit = min(limit or 20, 100)
    
    # Se entity_type específico, buscar apenas nele
    if entity_type:
        result = await _search_specific_entity(entity_type, query, limit, filters or {})
        if result["success"]:
            return result
        else:
            return {
                "success": False,
                "message": f"❌ Erro na busca em {entity_type}",
                "error": result.get("error"),
                "query": query,
                "entity_type": entity_type
            }
    
    # Busca universal em múltiplas entidades
    entities_to_search = [
        ("customers", "clientes"),
        ("creditors", "credores/fornecedores"), 
        ("projects", "empreendimentos/obras"),
        ("bills", "títulos a pagar"),
        ("purchase_orders", "pedidos de compra")
    ]
    
    total_found = 0
    
    for entity_key, entity_name in entities_to_search:
        try:
            entity_result = await _search_specific_entity(entity_key, query, min(5, limit), {})
            if entity_result["success"] and entity_result.get("count", 0) > 0:
                search_results.append({
                    "entity_type": entity_key,
                    "entity_name": entity_name,
                    "count": entity_result["count"],
                    "results": entity_result["data"][:5],  # Limitar a 5 por entidade na busca universal
                    "has_more": entity_result["count"] > 5
                })
                total_found += entity_result["count"]
        except Exception as e:
            # Continuar com outras entidades se uma falhar
            continue
    
    if search_results:
        return {
            "success": True,
            "message": f"✅ Busca '{query}' encontrou resultados em {len(search_results)} entidades (total: {total_found} registros)",
            "query": query,
            "total_entities": len(search_results),
            "total_records": total_found,
            "results_by_entity": search_results,
            "suggestion": "Use entity_type para buscar especificamente em uma entidade e obter mais resultados"
        }
    else:
        return {
            "success": False,
            "message": f"❌ Nenhum resultado encontrado para '{query}'",
            "query": query,
            "searched_entities": [name for _, name in entities_to_search],
            "suggestion": "Tente termos mais específicos ou use os tools específicos de cada entidade"
        }


async def _search_specific_entity(entity_type: str, query: str, limit: int, filters: Dict) -> Dict:
    """
    Função auxiliar para buscar em uma entidade específica
    CORRIGIDO: Usa serviços internos, nunca outras tools
    """
    
    if entity_type == "customers":
        result = await _svc_get_customers(limit=limit, search=query)
        if result["success"]:
            data = result["data"]
            customers = data.get("results", []) if isinstance(data, dict) else data
            return {
                "success": True,
                "data": customers,
                "count": len(customers),
                "entity_type": "customers"
            }
    
    elif entity_type == "creditors":
        result = await _svc_get_creditors(limit=limit, search=query)
        if result["success"]:
            data = result["data"]
            creditors = data.get("results", []) if isinstance(data, dict) else data
            return {
                "success": True,
                "data": creditors,
                "count": len(creditors),
                "entity_type": "creditors"
            }
    
    elif entity_type == "projects" or entity_type == "enterprises":
        # Para projetos, usar filtros mais específicos se disponível
        company_id = filters.get("company_id")
        result = await _svc_get_projects(limit=limit, company_id=company_id)
        if result["success"]:
            data = result["data"]
            projects = data.get("results", []) if isinstance(data, dict) else data
            
            # Filtrar por query se fornecida
            if query:
                projects = [
                    p for p in projects 
                    if query.lower() in str(p.get("description", "")).lower() 
                    or query.lower() in str(p.get("name", "")).lower()
                    or query.lower() in str(p.get("code", "")).lower()
                ]
            return {
                "success": True,
                "data": projects,
                "count": len(projects),
                "entity_type": "projects"
            }
    
    elif entity_type == "bills":
        # Para títulos, usar data padrão se não especificada
        start_date = filters.get("start_date")
        end_date = filters.get("end_date") 
        result = await _svc_get_bills(
            start_date=start_date, 
            end_date=end_date, 
            limit=limit
        )
        if result["success"]:
            data = result["data"]
            bills = data.get("results", []) if isinstance(data, dict) else data
            return {
                "success": True,
                "data": bills,
                "count": len(bills),
                "entity_type": "bills"
            }
    
    elif entity_type == "purchase_orders":
        result = await _svc_get_purchase_orders(limit=limit)
        if result["success"]:
            data = result["data"]
            orders = data.get("results", []) if isinstance(data, dict) else data
            
            # Filtrar por query se fornecida
            if query:
                orders = [
                    o for o in orders 
                    if query.lower() in str(o.get("description", "")).lower()
                    or query.lower() in str(o.get("id", "")).lower()
                ]
            return {
                "success": True,
                "data": orders,
                "count": len(orders),
                "entity_type": "purchase_orders"
            }
    
    # Se chegou aqui, entidade não suportada ou erro
    return {
        "success": False,
        "error": f"Entidade '{entity_type}' não suportada ou erro na busca",
        "supported_entities": ["customers", "creditors", "projects", "bills", "purchase_orders"]
    }


@mcp.tool
async def list_sienge_entities(_meta: Optional[Dict] = None) -> Dict:
    """
    Lista todas as entidades disponíveis no Sienge MCP para busca
    
    Retorna informações sobre os tipos de dados que podem ser consultados
    """
    entities = [
        {
            "type": "customers",
            "name": "Clientes",
            "description": "Clientes cadastrados no sistema",
            "search_fields": ["nome", "documento", "email"],
            "tools": ["get_sienge_customers", "search_sienge_data"]
        },
        {
            "type": "creditors", 
            "name": "Credores/Fornecedores",
            "description": "Fornecedores e credores cadastrados",
            "search_fields": ["nome", "documento"],
            "tools": ["get_sienge_creditors", "get_sienge_creditor_bank_info", "get_sienge_suppliers"]
        },
        {
            "type": "projects",
            "name": "Empreendimentos/Obras", 
            "description": "Projetos e obras cadastrados",
            "search_fields": ["código", "descrição", "nome"],
            "tools": ["get_sienge_projects", "get_sienge_enterprises", "get_sienge_enterprise_by_id"]
        },
        {
            "type": "bills",
            "name": "Títulos a Pagar",
            "description": "Contas a pagar e títulos financeiros",
            "search_fields": ["número", "credor", "valor"],
            "tools": ["get_sienge_bills", "get_sienge_accounts_payable"]
        },
        {
            "type": "purchase_orders",
            "name": "Pedidos de Compra",
            "description": "Pedidos de compra e solicitações",
            "search_fields": ["id", "descrição", "status"],
            "tools": ["get_sienge_purchase_orders", "get_sienge_purchase_requests", "list_sienge_purchase_requests"]
        },
        {
            "type": "invoices",
            "name": "Notas Fiscais",
            "description": "Notas fiscais de compra",
            "search_fields": ["número", "série", "fornecedor"],
            "tools": ["get_sienge_purchase_invoice"]
        },
        {
            "type": "stock",
            "name": "Estoque",
            "description": "Inventário e movimentações de estoque",
            "search_fields": ["centro_custo", "recurso"],
            "tools": ["get_sienge_stock_inventory", "get_sienge_stock_reservations"]
        },
        {
            "type": "financial",
            "name": "Financeiro",
            "description": "Contas a receber e movimentações financeiras",
            "search_fields": ["período", "cliente", "valor"],
            "tools": ["get_sienge_accounts_receivable", "search_sienge_financial_data", "search_sienge_finances"]
        },
        {
            "type": "suppliers",
            "name": "Fornecedores",
            "description": "Fornecedores e credores cadastrados", 
            "search_fields": ["código", "nome", "razão social"],
            "tools": ["get_sienge_suppliers"]
        }
    ]
    
    return {
        "success": True,
        "message": f"✅ {len(entities)} tipos de entidades disponíveis no Sienge",
        "entities": entities,
        "total_tools": sum(len(e["tools"]) for e in entities),
        "usage_example": {
            "search_all": "search_sienge_data('nome_cliente')",
            "search_specific": "search_sienge_data('nome_cliente', entity_type='customers')",
            "direct_access": "get_sienge_customers(search='nome_cliente')"
        }
    }


# ============ PAGINATION E NAVEGAÇÃO ============


@mcp.tool 
async def get_sienge_data_paginated(
    entity_type: str,
    page: int = 1,
    page_size: int = 20,
    filters: Optional[Dict[str, Any]] = None,
    sort_by: Optional[str] = None,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Busca dados do Sienge com paginação avançada - compatível com ChatGPT
    
    Args:
        entity_type: Tipo de entidade (customers, creditors, projects, bills, etc.)
        page: Número da página (começando em 1)
        page_size: Registros por página (máximo 50)
        filters: Filtros específicos da entidade
        sort_by: Campo para ordenação (se suportado)
    """
    page_size = min(page_size, 50)
    offset = (page - 1) * page_size
    
    filters = filters or {}
    
    # CORRIGIDO: Mapear para serviços internos, não tools
    if entity_type == "customers":
        search = filters.get("search")
        customer_type_id = filters.get("customer_type_id")
        result = await _svc_get_customers(
            limit=page_size,
            offset=offset, 
            search=search,
            customer_type_id=customer_type_id
        )
        # CORRIGIDO: Extrair items e total corretamente
        if result["success"]:
            data = result["data"]
            items, total = _extract_items_and_total(data)
            result["customers"] = items
            result["count"] = len(items)
            result["total_count"] = total
        
    elif entity_type == "creditors":
        search = filters.get("search")
        result = await _svc_get_creditors(
            limit=page_size,
            offset=offset,
            search=search
        )
        # CORRIGIDO: Extrair items e total corretamente
        if result["success"]:
            data = result["data"]
            items, total = _extract_items_and_total(data)
            result["creditors"] = items
            result["count"] = len(items)
            result["total_count"] = total
        
    elif entity_type == "projects":
        result = await _svc_get_projects(
            limit=page_size,
            offset=offset,
            company_id=filters.get("company_id"),
            enterprise_type=filters.get("enterprise_type")
        )
        # CORRIGIDO: Extrair items e total corretamente
        if result["success"]:
            data = result["data"]
            items, total = _extract_items_and_total(data)
            result["projects"] = items
            result["enterprises"] = items  # Para compatibilidade
            result["count"] = len(items)
            result["total_count"] = total
        
    elif entity_type == "bills":
        result = await _svc_get_bills(
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
            creditor_id=filters.get("creditor_id"),
            status=filters.get("status"),
            limit=page_size
        )
        # CORRIGIDO: Extrair items e total corretamente
        if result["success"]:
            data = result["data"]
            items, total = _extract_items_and_total(data)
            result["bills"] = items
            result["count"] = len(items)
            result["total_count"] = total
        
    else:
        return {
            "success": False,
            "message": f"❌ Tipo de entidade '{entity_type}' não suportado para paginação",
            "supported_types": ["customers", "creditors", "projects", "bills"]
        }
    
    if result["success"]:
        # Calcular informações de paginação
        total_count = result.get("total_count", result.get("count", 0))
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        
        return {
            "success": True,
            "message": f"✅ Página {page} de {total_pages} - {entity_type}",
            "data": result.get(entity_type, result.get("data", [])),
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "total_records": total_count,
                "has_next": page < total_pages,
                "has_previous": page > 1,
                "next_page": page + 1 if page < total_pages else None,
                "previous_page": page - 1 if page > 1 else None
            },
            "entity_type": entity_type,
            "filters_applied": filters
        }
    
    return result


@mcp.tool
async def search_sienge_financial_data(
    period_start: str,
    period_end: str, 
    search_type: str = "both",
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    customer_creditor_search: Optional[str] = None,
    _meta: Optional[Dict] = None) -> Dict:
    """
    Busca avançada em dados financeiros do Sienge - Contas a Pagar e Receber
    
    Args:
        period_start: Data inicial do período (YYYY-MM-DD)
        period_end: Data final do período (YYYY-MM-DD)
        search_type: Tipo de busca ("receivable", "payable", "both")
        amount_min: Valor mínimo (opcional)
        amount_max: Valor máximo (opcional)
        customer_creditor_search: Buscar por nome de cliente/credor (opcional)
    """
    
    financial_results = {
        "receivable": {"success": False, "data": [], "count": 0, "error": None},
        "payable": {"success": False, "data": [], "count": 0, "error": None}
    }
    
    # Buscar contas a receber
    if search_type in ["receivable", "both"]:
        try:
            # CORRIGIDO: Usar serviço interno
            receivable_result = await _svc_get_accounts_receivable(
                start_date=period_start,
                end_date=period_end,
                selection_type="D"  # Por vencimento
            )
            
            if receivable_result["success"]:
                receivable_data = receivable_result.get("data", [])
                
                # CORRIGIDO: Aplicar filtros de valor usando _parse_numeric_value
                if amount_min is not None or amount_max is not None:
                    filtered_data = []
                    for item in receivable_data:
                        amount = _parse_numeric_value(item.get("amount", 0))
                        if amount_min is not None and amount < amount_min:
                            continue
                        if amount_max is not None and amount > amount_max:
                            continue
                        filtered_data.append(item)
                    receivable_data = filtered_data
                
                # Aplicar filtro de cliente se especificado
                if customer_creditor_search:
                    search_lower = customer_creditor_search.lower()
                    filtered_data = []
                    for item in receivable_data:
                        customer_name = str(item.get("customer_name", "")).lower()
                        if search_lower in customer_name:
                            filtered_data.append(item)
                    receivable_data = filtered_data
                
                financial_results["receivable"] = {
                    "success": True,
                    "data": receivable_data,
                    "count": len(receivable_data),
                    "error": None
                }
            else:
                financial_results["receivable"]["error"] = receivable_result.get("error")
                
        except Exception as e:
            financial_results["receivable"]["error"] = str(e)
    
    # Buscar contas a pagar  
    if search_type in ["payable", "both"]:
        try:
            # CORRIGIDO: Usar serviço interno
            payable_result = await _svc_get_bills(
                start_date=period_start,
                end_date=period_end,
                limit=100
            )
            
            if payable_result["success"]:
                data = payable_result["data"]
                payable_data = data.get("results", []) if isinstance(data, dict) else data
                
                # CORRIGIDO: Aplicar filtros de valor usando _parse_numeric_value
                if amount_min is not None or amount_max is not None:
                    filtered_data = []
                    for item in payable_data:
                        amount = _parse_numeric_value(item.get("amount", 0))
                        if amount_min is not None and amount < amount_min:
                            continue
                        if amount_max is not None and amount > amount_max:
                            continue
                        filtered_data.append(item)
                    payable_data = filtered_data
                
                # Aplicar filtro de credor se especificado
                if customer_creditor_search:
                    search_lower = customer_creditor_search.lower()
                    filtered_data = []
                    for item in payable_data:
                        creditor_name = str(item.get("creditor_name", "")).lower()
                        if search_lower in creditor_name:
                            filtered_data.append(item)
                    payable_data = filtered_data
                
                financial_results["payable"] = {
                    "success": True,
                    "data": payable_data,
                    "count": len(payable_data),
                    "error": None
                }
            else:
                financial_results["payable"]["error"] = payable_result.get("error")
                
        except Exception as e:
            financial_results["payable"]["error"] = str(e)
    
    # Compilar resultado final
    total_records = financial_results["receivable"]["count"] + financial_results["payable"]["count"]
    has_errors = bool(financial_results["receivable"]["error"] or financial_results["payable"]["error"])
    
    summary = {
        "period": f"{period_start} a {period_end}",
        "search_type": search_type,
        "total_records": total_records,
        "receivable_count": financial_results["receivable"]["count"],
        "payable_count": financial_results["payable"]["count"],
        "filters_applied": {
            "amount_range": f"{amount_min or 'sem mín'} - {amount_max or 'sem máx'}",
            "customer_creditor": customer_creditor_search or "todos"
        }
    }
    
    if total_records > 0:
        return {
            "success": True,
            "message": f"✅ Busca financeira encontrou {total_records} registros no período",
            "summary": summary,
            "receivable": financial_results["receivable"],
            "payable": financial_results["payable"],
            "has_errors": has_errors
        }
    else:
        return {
            "success": False,
            "message": f"❌ Nenhum registro financeiro encontrado no período {period_start} a {period_end}",
            "summary": summary,
            "errors": {
                "receivable": financial_results["receivable"]["error"],
                "payable": financial_results["payable"]["error"]
            }
        }


@mcp.tool
async def get_sienge_dashboard_summary(_meta: Optional[Dict] = None) -> Dict:
    """
    Obtém um resumo tipo dashboard com informações gerais do Sienge
    Útil para visão geral rápida do sistema
    """
    
    # Data atual e períodos
    today = datetime.now()
    current_month_start = today.replace(day=1).strftime("%Y-%m-%d")
    current_month_end = today.strftime("%Y-%m-%d")
    
    dashboard_data = {}
    errors = []
    
    # 1. Testar conexão
    try:
        connection_test = await test_sienge_connection()
        dashboard_data["connection"] = connection_test
    except Exception as e:
        errors.append(f"Teste de conexão: {str(e)}")
        dashboard_data["connection"] = {"success": False, "error": str(e)}
    
    # 2. Contar clientes (amostra)
    try:
        # CORRIGIDO: Usar serviço interno
        customers_result = await _svc_get_customers(limit=1)
        dashboard_data["customers"] = {"available": customers_result["success"]}
    except Exception as e:
        errors.append(f"Clientes: {str(e)}")
        dashboard_data["customers"] = {"available": False}
    
    # 3. Contar projetos (amostra)
    try:
        # CORRIGIDO: Usar serviço interno
        projects_result = await _svc_get_projects(limit=5)
        if projects_result["success"]:
            data = projects_result["data"]
            enterprises = data.get("results", []) if isinstance(data, dict) else data
            metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
            
            dashboard_data["projects"] = {
                "available": True,
                "sample_count": len(enterprises),
                "total_count": metadata.get("count", "N/A")
            }
        else:
            dashboard_data["projects"] = {"available": False}
    except Exception as e:
        errors.append(f"Projetos: {str(e)}")
        dashboard_data["projects"] = {"available": False, "error": str(e)}
    
    # 4. Títulos a pagar do mês atual
    try:
        # CORRIGIDO: Usar serviço interno
        bills_result = await _svc_get_bills(
            start_date=current_month_start,
            end_date=current_month_end,
            limit=10
        )
        if bills_result["success"]:
            data = bills_result["data"]
            bills = data.get("results", []) if isinstance(data, dict) else data
            metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
            
            dashboard_data["monthly_bills"] = {
                "available": True,
                "count": len(bills),
                "total_count": metadata.get("count", len(bills))
            }
        else:
            dashboard_data["monthly_bills"] = {"available": False}
    except Exception as e:
        errors.append(f"Títulos mensais: {str(e)}")
        dashboard_data["monthly_bills"] = {"available": False, "error": str(e)}
    
    # 5. Tipos de clientes
    try:
        # CORRIGIDO: Usar serviço interno
        customer_types_result = await _svc_get_customer_types()
        if customer_types_result["success"]:
            data = customer_types_result["data"]
            customer_types = data.get("results", []) if isinstance(data, dict) else data
            
            dashboard_data["customer_types"] = {
                "available": True,
                "count": len(customer_types)
            }
        else:
            dashboard_data["customer_types"] = {"available": False}
    except Exception as e:
        dashboard_data["customer_types"] = {"available": False, "error": str(e)}
    
    # Compilar resultado
    available_modules = sum(1 for key, value in dashboard_data.items() 
                          if key != "connection" and isinstance(value, dict) and value.get("available"))
    
    return {
        "success": True,
        "message": f"✅ Dashboard do Sienge - {available_modules} módulos disponíveis",
        "timestamp": today.isoformat(),
        "period_analyzed": f"{current_month_start} a {current_month_end}",
        "modules_status": dashboard_data,
        "available_modules": available_modules,
        "errors": errors if errors else None,
        "quick_actions": [
            "search_sienge_data('termo_busca') - Busca universal",
            "list_sienge_entities() - Listar tipos de dados", 
            "get_sienge_customers(search='nome') - Buscar clientes",
            "get_sienge_projects() - Listar projetos/obras",
            "search_sienge_financial_data('2024-01-01', '2024-12-31') - Dados financeiros"
        ]
    }


# ============ UTILITÁRIOS ============


@mcp.tool
def add(a: int, b: int) -> int:
    """Soma dois números (função de teste)"""
    return a + b


def _mask(s: str) -> str:
    """Mascara dados sensíveis mantendo apenas o início e fim"""
    if not s:
        return None
    if len(s) == 1:
        return s + "*"
    if len(s) == 2:
        return s
    if len(s) <= 4:
        return s[:2] + "*" * (len(s) - 2)
    # Para strings > 4: usar no máximo 4 asteriscos no meio
    middle_asterisks = min(4, len(s) - 4)
    return s[:2] + "*" * middle_asterisks + s[-2:]


def _get_auth_info_internal() -> Dict:
    """Função interna para verificar configuração de autenticação"""
    if SIENGE_API_KEY and SIENGE_API_KEY != "sua_api_key_aqui":
        return {"auth_method": "Bearer Token", "configured": True, "base_url": SIENGE_BASE_URL, "api_key_configured": True}
    elif SIENGE_USERNAME and SIENGE_PASSWORD:
        return {
            "auth_method": "Basic Auth",
            "configured": True,
            "base_url": SIENGE_BASE_URL,
            "subdomain": SIENGE_SUBDOMAIN,
            "username": _mask(SIENGE_USERNAME) if SIENGE_USERNAME else None,
        }
    else:
        return {
            "auth_method": "None",
            "configured": False,
            "message": "Configure SIENGE_API_KEY ou SIENGE_USERNAME/PASSWORD no .env",
        }


@mcp.tool
def get_auth_info() -> Dict:
    """Retorna informações sobre a configuração de autenticação"""
    return _get_auth_info_internal()


def main():
    """Entry point for the Sienge MCP Server"""
    print("* Iniciando Sienge MCP Server (FastMCP)...")

    # Mostrar info de configuração
    auth_info = _get_auth_info_internal()
    print(f"* Autenticacao: {auth_info['auth_method']}")
    print(f"* Configurado: {auth_info['configured']}")

    if not auth_info["configured"]:
        print("* ERRO: Autenticacao nao configurada!")
        print("Configure as variáveis de ambiente:")
        print("- SIENGE_API_KEY (Bearer Token) OU")
        print("- SIENGE_USERNAME + SIENGE_PASSWORD + SIENGE_SUBDOMAIN (Basic Auth)")
        print("- SIENGE_BASE_URL (padrão: https://api.sienge.com.br)")
        print("")
        print("Exemplo no Windows PowerShell:")
        print('$env:SIENGE_USERNAME="seu_usuario"')
        print('$env:SIENGE_PASSWORD="sua_senha"')
        print('$env:SIENGE_SUBDOMAIN="sua_empresa"')
        print("")
        print("Exemplo no Linux/Mac:")
        print('export SIENGE_USERNAME="seu_usuario"')
        print('export SIENGE_PASSWORD="sua_senha"')
        print('export SIENGE_SUBDOMAIN="sua_empresa"')
    else:
        print("* MCP pronto para uso!")

    mcp.run()


if __name__ == "__main__":
    main()
