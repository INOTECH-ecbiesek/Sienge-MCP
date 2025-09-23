#!/usr/bin/env python3
"""
Script para testar as correções implementadas no server2.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from sienge_mcp.server2 import (
    _mask,
    to_camel_json,
    _extract_items_and_total,
    search_sienge_finances,
    get_sienge_suppliers,
    get_auth_info
)

def test_mask_function():
    """Testa a função de mascaramento"""
    print("🔐 Testando função _mask:")
    
    test_cases = [
        ("usuario123", "us****23"),
        ("admin", "ad**in"),
        ("ab", "ab"),
        ("a", "a*"),
        ("", None),
        (None, None)
    ]
    
    for input_val, expected in test_cases:
        try:
            result = _mask(input_val) if input_val else _mask(input_val) if input_val == "" else None
            print(f"  '{input_val}' → '{result}' (esperado: '{expected}')")
            if result != expected:
                print(f"    ❌ ERRO: Esperado '{expected}', obtido '{result}'")
            else:
                print(f"    ✅ OK")
        except Exception as e:
            print(f"    ❌ ERRO: {e}")

def test_camel_json():
    """Testa a normalização camelCase"""
    print("\n🐪 Testando normalização camelCase:")
    
    test_data = {
        "purchase_order_id": 123,
        "supplier_info": {
            "company_name": "Test Corp",
            "tax_id": "12345678000190"
        },
        "line_items": [
            {"item_code": "ABC", "unit_price": 10.50}
        ]
    }
    
    try:
        result = to_camel_json(test_data)
        print(f"  Input: {test_data}")
        print(f"  Output: {result}")
        
        # Verificar se as chaves foram convertidas
        expected_keys = ["purchaseOrderId", "supplierInfo", "lineItems"]
        for key in expected_keys:
            if key in str(result):
                print(f"    ✅ '{key}' encontrado")
            else:
                print(f"    ❌ '{key}' NÃO encontrado")
                
    except Exception as e:
        print(f"    ❌ ERRO: {e}")

def test_extract_items_and_total():
    """Testa extração de itens e total"""
    print("\n📊 Testando extração de metadados:")
    
    # Simular resposta da API
    api_response = {
        "results": [{"id": 1}, {"id": 2}, {"id": 3}],
        "resultSetMetadata": {
            "count": 150,
            "hasNext": True
        }
    }
    
    try:
        items, total_count = _extract_items_and_total(api_response)
        print(f"  Input: {api_response}")
        print(f"  Items extraídos: {len(items)}")
        print(f"  Total count: {total_count}")
        
        if len(items) == 3 and total_count == 150:
            print("    ✅ Extração correta")
        else:
            print("    ❌ Extração incorreta")
            
    except Exception as e:
        print(f"    ❌ ERRO: {e}")

def test_auth_info():
    """Testa informações de autenticação mascaradas"""
    print("\n🔑 Testando get_auth_info (sem credenciais reais):")
    
    try:
        auth_info = get_auth_info()
        print(f"  Resultado: {auth_info}")
        
        if "configured" in auth_info:
            print("    ✅ Estrutura correta")
        else:
            print("    ❌ Estrutura incorreta")
            
    except Exception as e:
        print(f"    ❌ ERRO: {e}")

def test_amount_filter_parsing():
    """Testa o parsing de filtros de valor na função search_sienge_finances"""
    print("\n💰 Testando parsing de amount_filter:")
    
    # Não podemos testar a função completa sem credenciais, mas podemos 
    # testar a lógica de parsing criando uma versão simplificada
    
    test_filters = [
        "100..500",
        ">=1000", 
        "<=500",
        ">100",
        "<200",
        "=750",
        "1000",
        "invalid_filter"
    ]
    
    for filter_str in test_filters:
        print(f"  Testando '{filter_str}':")
        
        # Replicar a lógica de parsing da função
        amount_min = amount_max = None
        if filter_str:
            s = filter_str.replace(" ", "")
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
                    amount_min = float(s[1:])
                elif s.startswith("<"):
                    amount_max = float(s[1:])
                elif s.startswith("="):
                    v = float(s[1:])
                    amount_min = v
                    amount_max = v
                else:
                    amount_min = float(s)
            except ValueError:
                amount_min = amount_max = None
        
        print(f"    → min: {amount_min}, max: {amount_max}")

if __name__ == "__main__":
    print("🚀 Iniciando testes das correções implementadas...\n")
    
    test_mask_function()
    test_camel_json() 
    test_extract_items_and_total()
    test_auth_info()
    test_amount_filter_parsing()
    
    print("\n✅ Testes concluídos!")