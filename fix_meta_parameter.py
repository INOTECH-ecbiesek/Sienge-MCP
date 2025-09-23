#!/usr/bin/env python3
"""
Script para adicionar o parâmetro _meta opcional em todas as funções @mcp.tool
para resolver o erro de validação do Pydantic
"""

import re

def fix_mcp_tool_functions(file_path):
    """Adiciona _meta: Optional[Dict] = None em todas as funções @mcp.tool"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Padrão para encontrar funções @mcp.tool
    pattern = r'(@mcp\.tool\s*\n)(async def\s+\w+\s*\([^)]*)\) -> Dict:'
    
    def replace_function(match):
        decorator = match.group(1)
        func_signature = match.group(2)
        
        # Se já tem _meta, não modificar
        if '_meta:' in func_signature:
            return match.group(0)
        
        # Se a função não tem parâmetros, adicionar apenas _meta
        if func_signature.strip().endswith('('):
            new_signature = func_signature + '_meta: Optional[Dict] = None'
        else:
            # Se tem parâmetros, adicionar _meta no final
            new_signature = func_signature + ',\n    _meta: Optional[Dict] = None'
        
        return decorator + new_signature + ') -> Dict:'
    
    # Aplicar a correção
    fixed_content = re.sub(pattern, replace_function, content, flags=re.MULTILINE)
    
    # Verificar quantas mudanças foram feitas
    changes = len(re.findall(pattern, content))
    
    # Salvar o arquivo corrigido
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    return changes

if __name__ == "__main__":
    file_path = r"c:\Users\Moizes-Pc\Desktop\Sienge\Sienge-MCP\src\sienge_mcp\server2.py"
    
    print("🔧 Aplicando correção do parâmetro _meta...")
    changes = fix_mcp_tool_functions(file_path)
    print(f"✅ {changes} funções corrigidas!")
    print("Todas as funções @mcp.tool agora aceitam o parâmetro _meta opcional.")