#!/usr/bin/env python3
"""
Script final para corrigir todos os problemas de sintaxe
"""

import re

def fix_all_syntax(file_path):
    """Corrige todos os problemas de sintaxe"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Corrigir vírgulas extras antes de _meta
    content = re.sub(r',\s*\n\s*,\s*\n\s*_meta:', r',\n    _meta:', content, flags=re.MULTILINE)
    
    # 2. Corrigir linhas que são apenas vírgulas seguidas de _meta
    content = re.sub(r'^\s*,\s*\n\s*_meta:', r'    _meta:', content, flags=re.MULTILINE)
    
    # 3. Corrigir parâmetros sem vírgula antes de _meta (caso não haja outros parâmetros)
    content = re.sub(r'\(\s*\n\s*_meta: Optional\[Dict\] = None\)', r'(_meta: Optional[Dict] = None)', content, flags=re.MULTILINE)
    
    # Salvar o arquivo corrigido
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

if __name__ == "__main__":
    file_path = r"c:\Users\Moizes-Pc\Desktop\Sienge\Sienge-MCP\src\sienge_mcp\server2.py"
    
    print("🔧 Aplicando correção final de sintaxe...")
    fix_all_syntax(file_path)
    print("✅ Correção final aplicada!")