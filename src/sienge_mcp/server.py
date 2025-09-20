#!/usr/bin/env python3
"""
SIENGE MCP COMPLETO - FastMCP com Autenticação Flexível
Suporta Bearer Token e Basic Auth
"""

from fastmcp import FastMCP
import httpx
from typing import Dict, List, Optional, Any
import os
from dotenv import load_dotenv
from datetime import datetime

# Carrega as variáveis de ambiente
load_dotenv()

mcp = FastMCP("Sienge API Integration 🏗️")

# Configurações da API do Sienge
SIENGE_BASE_URL = os.getenv("SIENGE_BASE_URL", "https://api.sienge.com.br")
SIENGE_SUBDOMAIN = os.getenv("SIENGE_SUBDOMAIN", "")
SIENGE_USERNAME = os.getenv("SIENGE_USERNAME", "")
SIENGE_PASSWORD = os.getenv("SIENGE_PASSWORD", "")
SIENGE_API_KEY = os.getenv("SIENGE_API_KEY", "")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))


class SiengeAPIError(Exception):
    """Exceção customizada para erros da API do Sienge"""

    pass


async def make_sienge_request(
    method: str, endpoint: str, params: Optional[Dict] = None, json_data: Optional[Dict] = None
) -> Dict:
    """
    Função auxiliar para fazer requisições à API do Sienge (v1)
    Suporta tanto Bearer Token quanto Basic Auth
    """
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}

            # Configurar autenticação e URL
            auth = None

            if SIENGE_API_KEY and SIENGE_API_KEY != "sua_api_key_aqui":
                # Bearer Token (Recomendado)
                headers["Authorization"] = f"Bearer {SIENGE_API_KEY}"
                url = f"{SIENGE_BASE_URL}/{SIENGE_SUBDOMAIN}/public/api/v1{endpoint}"
            elif SIENGE_USERNAME and SIENGE_PASSWORD:
                # Basic Auth usando httpx.BasicAuth
                auth = httpx.BasicAuth(SIENGE_USERNAME, SIENGE_PASSWORD)
                url = f"{SIENGE_BASE_URL}/{SIENGE_SUBDOMAIN}/public/api/v1{endpoint}"
            else:
                return {
                    "success": False,
                    "error": "No Authentication",
                    "message": "Configure SIENGE_API_KEY ou SIENGE_USERNAME/PASSWORD no .env",
                }

            response = await client.request(method=method, url=url, headers=headers, params=params, json=json_data, auth=auth)

            if response.status_code in [200, 201]:
                try:
                    return {"success": True, "data": response.json(), "status_code": response.status_code}
                except BaseException:
                    return {"success": True, "data": {"message": "Success"}, "status_code": response.status_code}
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "message": response.text,
                    "status_code": response.status_code,
                }

    except httpx.TimeoutException:
        return {"success": False, "error": "Timeout", "message": f"A requisição excedeu o tempo limite de {REQUEST_TIMEOUT}s"}
    except Exception as e:
        return {"success": False, "error": str(e), "message": f"Erro na requisição: {str(e)}"}


async def make_sienge_bulk_request(
    method: str, endpoint: str, params: Optional[Dict] = None, json_data: Optional[Dict] = None
) -> Dict:
    """
    Função auxiliar para fazer requisições à API bulk-data do Sienge
    Suporta tanto Bearer Token quanto Basic Auth
    """
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}

            # Configurar autenticação e URL para bulk-data
            auth = None

            if SIENGE_API_KEY and SIENGE_API_KEY != "sua_api_key_aqui":
                # Bearer Token (Recomendado)
                headers["Authorization"] = f"Bearer {SIENGE_API_KEY}"
                url = f"{SIENGE_BASE_URL}/{SIENGE_SUBDOMAIN}/public/api/bulk-data/v1{endpoint}"
            elif SIENGE_USERNAME and SIENGE_PASSWORD:
                # Basic Auth usando httpx.BasicAuth
                auth = httpx.BasicAuth(SIENGE_USERNAME, SIENGE_PASSWORD)
                url = f"{SIENGE_BASE_URL}/{SIENGE_SUBDOMAIN}/public/api/bulk-data/v1{endpoint}"
            else:
                return {
                    "success": False,
                    "error": "No Authentication",
                    "message": "Configure SIENGE_API_KEY ou SIENGE_USERNAME/PASSWORD no .env",
                }

            response = await client.request(method=method, url=url, headers=headers, params=params, json=json_data, auth=auth)

            if response.status_code in [200, 201]:
                try:
                    return {"success": True, "data": response.json(), "status_code": response.status_code}
                except BaseException:
                    return {"success": True, "data": {"message": "Success"}, "status_code": response.status_code}
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "message": response.text,
                    "status_code": response.status_code,
                }

    except httpx.TimeoutException:
        return {"success": False, "error": "Timeout", "message": f"A requisição excedeu o tempo limite de {REQUEST_TIMEOUT}s"}
    except Exception as e:
        return {"success": False, "error": str(e), "message": f"Erro na requisição bulk-data: {str(e)}"}


# ============ CONEXÃO E TESTE ============


@mcp.tool
async def test_sienge_connection() -> Dict:
    """Testa a conexão com a API do Sienge"""
    try:
        # Tentar endpoint mais simples primeiro
        result = await make_sienge_request("GET", "/customer-types")

        if result["success"]:
            auth_method = "Bearer Token" if SIENGE_API_KEY else "Basic Auth"
            return {
                "success": True,
                "message": "✅ Conexão com API do Sienge estabelecida com sucesso!",
                "api_status": "Online",
                "auth_method": auth_method,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            return {
                "success": False,
                "message": "❌ Falha ao conectar com API do Sienge",
                "error": result.get("error"),
                "details": result.get("message"),
                "timestamp": datetime.now().isoformat(),
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
    limit: Optional[int] = 50, offset: Optional[int] = 0, search: Optional[str] = None, customer_type_id: Optional[str] = None
) -> Dict:
    """
    Busca clientes no Sienge com filtros

    Args:
        limit: Máximo de registros (padrão: 50)
        offset: Pular registros (padrão: 0)
        search: Buscar por nome ou documento
        customer_type_id: Filtrar por tipo de cliente
    """
    params = {"limit": min(limit or 50, 200), "offset": offset or 0}

    if search:
        params["search"] = search
    if customer_type_id:
        params["customer_type_id"] = customer_type_id

    result = await make_sienge_request("GET", "/customers", params=params)

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
            "filters_applied": params,
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar clientes",
        "error": result.get("error"),
        "details": result.get("message"),
    }


@mcp.tool
async def get_sienge_customer_types() -> Dict:
    """Lista tipos de clientes disponíveis"""
    result = await make_sienge_request("GET", "/customer-types")

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
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar tipos de clientes",
        "error": result.get("error"),
        "details": result.get("message"),
    }


# ============ CREDORES ============


@mcp.tool
async def get_sienge_creditors(limit: Optional[int] = 50, offset: Optional[int] = 0, search: Optional[str] = None) -> Dict:
    """
    Busca credores/fornecedores

    Args:
        limit: Máximo de registros (padrão: 50)
        offset: Pular registros (padrão: 0)
        search: Buscar por nome
    """
    params = {"limit": min(limit or 50, 200), "offset": offset or 0}
    if search:
        params["search"] = search

    result = await make_sienge_request("GET", "/creditors", params=params)

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
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar credores",
        "error": result.get("error"),
        "details": result.get("message"),
    }


@mcp.tool
async def get_sienge_creditor_bank_info(creditor_id: str) -> Dict:
    """
    Consulta informações bancárias de um credor

    Args:
        creditor_id: ID do credor (obrigatório)
    """
    result = await make_sienge_request("GET", f"/creditors/{creditor_id}/bank-informations")

    if result["success"]:
        return {
            "success": True,
            "message": f"✅ Informações bancárias do credor {creditor_id}",
            "creditor_id": creditor_id,
            "bank_info": result["data"],
        }

    return {
        "success": False,
        "message": f"❌ Erro ao buscar info bancária do credor {creditor_id}",
        "error": result.get("error"),
        "details": result.get("message"),
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
) -> Dict:
    """
    Consulta parcelas do contas a receber via API bulk-data

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
    params = {"startDate": start_date, "endDate": end_date, "selectionType": selection_type}

    if company_id:
        params["companyId"] = company_id
    if cost_centers_id:
        params["costCentersId"] = cost_centers_id
    if correction_indexer_id:
        params["correctionIndexerId"] = correction_indexer_id
    if correction_date:
        params["correctionDate"] = correction_date
    if change_start_date:
        params["changeStartDate"] = change_start_date
    if completed_bills:
        params["completedBills"] = completed_bills
    if origins_ids:
        params["originsIds"] = origins_ids
    if bearers_id_in:
        params["bearersIdIn"] = bearers_id_in
    if bearers_id_not_in:
        params["bearersIdNotIn"] = bearers_id_not_in

    result = await make_sienge_bulk_request("GET", "/income", params=params)

    if result["success"]:
        data = result["data"]
        income_data = data.get("data", []) if isinstance(data, dict) else data

        return {
            "success": True,
            "message": f"✅ Encontradas {len(income_data)} parcelas a receber",
            "income_data": income_data,
            "count": len(income_data),
            "period": f"{start_date} a {end_date}",
            "selection_type": selection_type,
            "filters": params,
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar parcelas a receber",
        "error": result.get("error"),
        "details": result.get("message"),
    }


@mcp.tool
async def get_sienge_accounts_receivable_by_bills(
    bills_ids: List[int], correction_indexer_id: Optional[int] = None, correction_date: Optional[str] = None
) -> Dict:
    """
    Consulta parcelas dos títulos informados via API bulk-data

    Args:
        bills_ids: Lista de códigos dos títulos - OBRIGATÓRIO
        correction_indexer_id: Código do indexador de correção
        correction_date: Data para correção do indexador (YYYY-MM-DD)
    """
    params = {"billsIds": bills_ids}

    if correction_indexer_id:
        params["correctionIndexerId"] = correction_indexer_id
    if correction_date:
        params["correctionDate"] = correction_date

    result = await make_sienge_bulk_request("GET", "/income/by-bills", params=params)

    if result["success"]:
        data = result["data"]
        income_data = data.get("data", []) if isinstance(data, dict) else data

        return {
            "success": True,
            "message": f"✅ Encontradas {len(income_data)} parcelas dos títulos informados",
            "income_data": income_data,
            "count": len(income_data),
            "bills_consulted": bills_ids,
            "filters": params,
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar parcelas dos títulos informados",
        "error": result.get("error"),
        "details": result.get("message"),
    }


@mcp.tool
async def get_sienge_bills(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    creditor_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: Optional[int] = 50,
) -> Dict:
    """
    Consulta títulos a pagar (contas a pagar) - REQUER startDate obrigatório

    Args:
        start_date: Data inicial obrigatória (YYYY-MM-DD) - padrão últimos 30 dias
        end_date: Data final (YYYY-MM-DD) - padrão hoje
        creditor_id: ID do credor
        status: Status do título (ex: open, paid, cancelled)
        limit: Máximo de registros (padrão: 50, máx: 200)
    """
    from datetime import datetime, timedelta

    # Se start_date não fornecido, usar últimos 30 dias
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    # Se end_date não fornecido, usar hoje
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # Parâmetros obrigatórios
    params = {"startDate": start_date, "endDate": end_date, "limit": min(limit or 50, 200)}  # OBRIGATÓRIO pela API

    # Parâmetros opcionais
    if creditor_id:
        params["creditor_id"] = creditor_id
    if status:
        params["status"] = status

    result = await make_sienge_request("GET", "/bills", params=params)

    if result["success"]:
        data = result["data"]
        bills = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}
        total_count = metadata.get("count", len(bills))

        return {
            "success": True,
            "message": f"✅ Encontrados {len(bills)} títulos a pagar (total: {total_count}) - período: {start_date} a {end_date}",
            "bills": bills,
            "count": len(bills),
            "total_count": total_count,
            "period": {"start_date": start_date, "end_date": end_date},
            "filters": params,
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar títulos a pagar",
        "error": result.get("error"),
        "details": result.get("message"),
    }


# ============ COMPRAS ============


@mcp.tool
async def get_sienge_purchase_orders(
    purchase_order_id: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    limit: Optional[int] = 50,
) -> Dict:
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
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar pedidos de compra",
        "error": result.get("error"),
        "details": result.get("message"),
    }


@mcp.tool
async def get_sienge_purchase_order_items(purchase_order_id: str) -> Dict:
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
async def get_sienge_purchase_requests(purchase_request_id: Optional[str] = None, limit: Optional[int] = 50) -> Dict:
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
async def create_sienge_purchase_request(description: str, project_id: str, items: List[Dict[str, Any]]) -> Dict:
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

    result = await make_sienge_request("POST", "/purchase-requests", json_data=request_data)

    if result["success"]:
        return {
            "success": True,
            "message": "✅ Solicitação de compra criada com sucesso",
            "request_id": result["data"].get("id"),
            "data": result["data"],
        }

    return {
        "success": False,
        "message": "❌ Erro ao criar solicitação de compra",
        "error": result.get("error"),
        "details": result.get("message"),
    }


# ============ NOTAS FISCAIS DE COMPRA ============


@mcp.tool
async def get_sienge_purchase_invoice(sequential_number: int) -> Dict:
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
async def get_sienge_purchase_invoice_items(sequential_number: int) -> Dict:
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
) -> Dict:
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
        "documentId": document_id,
        "number": number,
        "supplierId": supplier_id,
        "companyId": company_id,
        "movementTypeId": movement_type_id,
        "movementDate": movement_date,
        "issueDate": issue_date,
    }

    if series:
        invoice_data["series"] = series
    if notes:
        invoice_data["notes"] = notes

    result = await make_sienge_request("POST", "/purchase-invoices", json_data=invoice_data)

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
) -> Dict:
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
        "deliveriesOrder": deliveries_order,
        "copyNotesPurchaseOrders": copy_notes_purchase_orders,
        "copyNotesResources": copy_notes_resources,
        "copyAttachmentsPurchaseOrders": copy_attachments_purchase_orders,
    }

    result = await make_sienge_request(
        "POST", f"/purchase-invoices/{sequential_number}/items/purchase-orders/delivery-schedules", json_data=item_data
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
) -> Dict:
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
async def get_sienge_stock_inventory(cost_center_id: str, resource_id: Optional[str] = None) -> Dict:
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
async def get_sienge_stock_reservations(limit: Optional[int] = 50) -> Dict:
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
) -> Dict:
    """
    Busca empreendimentos/obras no Sienge

    Args:
        limit: Máximo de registros (padrão: 100, máximo: 200)
        offset: Pular registros (padrão: 0)
        company_id: Código da empresa
        enterprise_type: Tipo do empreendimento (1: Obra e Centro de custo, 2: Obra, 3: Centro de custo, 4: Centro de custo associado a obra)
        receivable_register: Filtro de registro de recebíveis (B3, CERC)
        only_buildings_enabled: Retornar apenas obras habilitadas para integração orçamentária
    """
    params = {"limit": min(limit or 100, 200), "offset": offset or 0}

    if company_id:
        params["companyId"] = company_id
    if enterprise_type:
        params["type"] = enterprise_type
    if receivable_register:
        params["receivableRegister"] = receivable_register
    if only_buildings_enabled:
        params["onlyBuildingsEnabledForIntegration"] = only_buildings_enabled

    result = await make_sienge_request("GET", "/enterprises", params=params)

    if result["success"]:
        data = result["data"]
        enterprises = data.get("results", []) if isinstance(data, dict) else data
        metadata = data.get("resultSetMetadata", {}) if isinstance(data, dict) else {}

        return {
            "success": True,
            "message": f"✅ Encontrados {len(enterprises)} empreendimentos",
            "enterprises": enterprises,
            "count": len(enterprises),
            "metadata": metadata,
            "filters": params,
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar empreendimentos",
        "error": result.get("error"),
        "details": result.get("message"),
    }


@mcp.tool
async def get_sienge_enterprise_by_id(enterprise_id: int) -> Dict:
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
async def get_sienge_enterprise_groupings(enterprise_id: int) -> Dict:
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
async def get_sienge_units(limit: Optional[int] = 50, offset: Optional[int] = 0) -> Dict:
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
        }

    return {
        "success": False,
        "message": "❌ Erro ao buscar unidades",
        "error": result.get("error"),
        "details": result.get("message"),
    }


# ============ CUSTOS ============


@mcp.tool
async def get_sienge_unit_cost_tables(
    table_code: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = "Active",
    integration_enabled: Optional[bool] = None,
) -> Dict:
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


# ============ UTILITÁRIOS ============


@mcp.tool
def add(a: int, b: int) -> int:
    """Soma dois números (função de teste)"""
    return a + b


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
            "username": SIENGE_USERNAME,
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
