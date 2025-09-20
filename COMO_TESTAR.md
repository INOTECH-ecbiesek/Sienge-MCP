# 🧪 TESTE LOCAL SIENGE ECBIESEK MCP

## ✅ **COMO TESTAR LOCALMENTE (SEM PYPI)**

### **1. Configurar Claude Desktop**

Edite o arquivo: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "SiengeECBIESEK_LOCAL": {
      "command": "C:\\Users\\Moizes\\Desktop\\SiengeMCP\\Sienge-mcp\\.venv\\Scripts\\sienge-ecbiesek-mcp.exe",
      "env": {
        "SIENGE_BASE_URL": "https://api.sienge.com.br",
        "SIENGE_SUBDOMAIN": "ecbiesek",
        "SIENGE_USERNAME": "SEU_USUARIO_REAL_AQUI",
        "SIENGE_PASSWORD": "SUA_SENHA_REAL_AQUI"
      }
    }
  }
}
```

### **2. Substituir Credenciais**
- Coloque seu usuário real do Sienge ECBIESEK
- Coloque sua senha real do Sienge ECBIESEK

### **3. Reiniciar Claude Desktop**
- Feche completamente o Claude Desktop
- Abra novamente
- O MCP deve aparecer nas ferramentas disponíveis

### **4. Testar**
Pergunte ao Claude:
- "Liste os projetos da ECBIESEK no Sienge"
- "Mostre as contas a pagar em aberto"
- "Quais colaboradores estão cadastrados?"

---

## 🌐 **OPÇÕES DE DISTRIBUIÇÃO**

### **OPÇÃO A: PyPI Público**
```bash
# Criar conta em https://pypi.org
# Depois:
.\.venv\Scripts\twine.exe upload dist/sienge_ecbiesek_mcp-1.0.0-py3-none-any.whl
```

### **OPÇÃO B: PyPI Privado/Interno**
- Configurar servidor PyPI interno da empresa
- Distribuir apenas internamente na ECBIESEK

### **OPÇÃO C: Distribuição Manual**
- Compartilhar o arquivo `.whl` internamente
- Equipe instala com: `pip install sienge_ecbiesek_mcp-1.0.0-py3-none-any.whl`

---

## 🎯 **RECOMENDAÇÃO IMEDIATA**

**TESTE PRIMEIRO LOCALMENTE** para verificar se funciona com suas credenciais reais do Sienge ECBIESEK antes de distribuir!
