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

mcp = FastMCP("Sienge API Integration 🏗️ - ChatGPT Compatible")

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


# ============ SEARCH UNIVERSAL (COMPATIBILIDADE CHATGPT) ============


@mcp.tool
async def search_sienge_data(
    query: str,
    entity_type: Optional[str] = None,
    limit: Optional[int] = 20,
    filters: Optional[Dict[str, Any]] = None
) -> Dict:
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
    """Função auxiliar para buscar em uma entidade específica"""
    
    if entity_type == "customers":
        result = await get_sienge_customers(limit=limit, search=query)
        if result["success"]:
            return {
                "success": True,
                "data": result["customers"],
                "count": result["count"],
                "entity_type": "customers"
            }
    
    elif entity_type == "creditors":
        result = await get_sienge_creditors(limit=limit, search=query)
        if result["success"]:
            return {
                "success": True,
                "data": result["creditors"],
                "count": result["count"],
                "entity_type": "creditors"
            }
    
    elif entity_type == "projects" or entity_type == "enterprises":
        # Para projetos, usar filtros mais específicos se disponível
        company_id = filters.get("company_id")
        result = await get_sienge_projects(limit=limit, company_id=company_id)
        if result["success"]:
            # Filtrar por query se fornecida
            projects = result["enterprises"]
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
        result = await get_sienge_bills(
            start_date=start_date, 
            end_date=end_date, 
            limit=limit
        )
        if result["success"]:
            return {
                "success": True,
                "data": result["bills"],
                "count": result["count"],
                "entity_type": "bills"
            }
    
    elif entity_type == "purchase_orders":
        result = await get_sienge_purchase_orders(limit=limit)
        if result["success"]:
            orders = result["purchase_orders"]
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
async def list_sienge_entities() -> Dict:
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
            "tools": ["get_sienge_creditors", "get_sienge_creditor_bank_info"]
        },
        {
            "type": "projects",
            "name": "Empreendimentos/Obras", 
            "description": "Projetos e obras cadastrados",
            "search_fields": ["código", "descrição", "nome"],
            "tools": ["get_sienge_projects", "get_sienge_enterprise_by_id"]
        },
        {
            "type": "bills",
            "name": "Títulos a Pagar",
            "description": "Contas a pagar e títulos financeiros",
            "search_fields": ["número", "credor", "valor"],
            "tools": ["get_sienge_bills"]
        },
        {
            "type": "purchase_orders",
            "name": "Pedidos de Compra",
            "description": "Pedidos de compra e solicitações",
            "search_fields": ["id", "descrição", "status"],
            "tools": ["get_sienge_purchase_orders", "get_sienge_purchase_requests"]
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
            "tools": ["get_sienge_accounts_receivable"]
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
    sort_by: Optional[str] = None
) -> Dict:
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
    
    # Mapear para os tools existentes com offset
    if entity_type == "customers":
        search = filters.get("search")
        customer_type_id = filters.get("customer_type_id")
        result = await get_sienge_customers(
            limit=page_size,
            offset=offset, 
            search=search,
            customer_type_id=customer_type_id
        )
        
    elif entity_type == "creditors":
        search = filters.get("search")
        result = await get_sienge_creditors(
            limit=page_size,
            offset=offset,
            search=search
        )
        
    elif entity_type == "projects":
        result = await get_sienge_projects(
            limit=page_size,
            offset=offset,
            company_id=filters.get("company_id"),
            enterprise_type=filters.get("enterprise_type")
        )
        
    elif entity_type == "bills":
        result = await get_sienge_bills(
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
            creditor_id=filters.get("creditor_id"),
            status=filters.get("status"),
            limit=page_size
        )
        
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
    customer_creditor_search: Optional[str] = None
) -> Dict:
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
            receivable_result = await get_sienge_accounts_receivable(
                start_date=period_start,
                end_date=period_end,
                selection_type="D"  # Por vencimento
            )
            
            if receivable_result["success"]:
                receivable_data = receivable_result["income_data"]
                
                # Aplicar filtros de valor se especificados
                if amount_min is not None or amount_max is not None:
                    filtered_data = []
                    for item in receivable_data:
                        amount = float(item.get("amount", 0) or 0)
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
            payable_result = await get_sienge_bills(
                start_date=period_start,
                end_date=period_end,
                limit=100
            )
            
            if payable_result["success"]:
                payable_data = payable_result["bills"]
                
                # Aplicar filtros de valor se especificados
                if amount_min is not None or amount_max is not None:
                    filtered_data = []
                    for item in payable_data:
                        amount = float(item.get("amount", 0) or 0)
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
async def get_sienge_dashboard_summary() -> Dict:
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
        customers_result = await get_sienge_customers(limit=1)
        if customers_result["success"]:
            dashboard_data["customers_available"] = True
        else:
            dashboard_data["customers_available"] = False
    except Exception as e:
        errors.append(f"Clientes: {str(e)}")
        dashboard_data["customers_available"] = False
    
    # 3. Contar projetos (amostra)
    try:
        projects_result = await get_sienge_projects(limit=5)
        if projects_result["success"]:
            dashboard_data["projects"] = {
                "available": True,
                "sample_count": len(projects_result["enterprises"]),
                "total_count": projects_result.get("metadata", {}).get("count", "N/A")
            }
        else:
            dashboard_data["projects"] = {"available": False}
    except Exception as e:
        errors.append(f"Projetos: {str(e)}")
        dashboard_data["projects"] = {"available": False, "error": str(e)}
    
    # 4. Títulos a pagar do mês atual
    try:
        bills_result = await get_sienge_bills(
            start_date=current_month_start,
            end_date=current_month_end,
            limit=10
        )
        if bills_result["success"]:
            dashboard_data["monthly_bills"] = {
                "available": True,
                "count": len(bills_result["bills"]),
                "total_count": bills_result.get("total_count", len(bills_result["bills"]))
            }
        else:
            dashboard_data["monthly_bills"] = {"available": False}
    except Exception as e:
        errors.append(f"Títulos mensais: {str(e)}")
        dashboard_data["monthly_bills"] = {"available": False, "error": str(e)}
    
    # 5. Tipos de clientes
    try:
        customer_types_result = await get_sienge_customer_types()
        if customer_types_result["success"]:
            dashboard_data["customer_types"] = {
                "available": True,
                "count": len(customer_types_result["customer_types"])
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
