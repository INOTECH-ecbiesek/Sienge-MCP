#!/usr/bin/env python3
"""
Script para corrigir vírgulas extras introduzidas pela primeira correção
"""

def fix_extra_commas(file_path):
    """Remove vírgulas extras"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Padrão para encontrar vírgulas extras antes de _meta
    pattern = r',\s*\n\s*,\s*\n\s*_meta: Optional\[Dict\] = None'
    replacement = r',\n    _meta: Optional[Dict] = None'
    
    # Aplicar a correção
    fixed_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Contar quantas mudanças foram feitas
    changes = len(re.findall(pattern, content))
    
    # Salvar o arquivo corrigido
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    return changes

import re

if __name__ == "__main__":
    file_path = r"c:\Users\Moizes-Pc\Desktop\Sienge\Sienge-MCP\src\sienge_mcp\server2.py"
    
    print("🔧 Corrigindo vírgulas extras...")
    changes = fix_extra_commas(file_path)
    print(f"✅ {changes} vírgulas extras corrigidas!")