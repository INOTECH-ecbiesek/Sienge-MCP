#!/usr/bin/env python3
"""
Script para corrigir especificamente as vírgulas que faltam antes de _meta
"""

import re

def fix_missing_commas(file_path):
    """Adiciona vírgulas que faltam antes de _meta"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Padrão para encontrar parâmetros sem vírgula antes de _meta
    # Busca por qualquer caractere que não seja vírgula, seguido de quebra de linha e _meta
    pattern = r'([^,\s])\s*\n\s*_meta: Optional\[Dict\] = None'
    replacement = r'\1,\n    _meta: Optional[Dict] = None'
    
    # Aplicar a correção
    fixed_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Contar quantas mudanças foram feitas
    matches = re.findall(pattern, content)
    changes = len(matches)
    
    # Salvar o arquivo corrigido
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    return changes

if __name__ == "__main__":
    file_path = r"c:\Users\Moizes-Pc\Desktop\Sienge\Sienge-MCP\src\sienge_mcp\server2.py"
    
    print("🔧 Corrigindo vírgulas que faltam antes de _meta...")
    changes = fix_missing_commas(file_path)
    print(f"✅ {changes} vírgulas adicionadas!")