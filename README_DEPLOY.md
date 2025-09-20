# 🚀 Deploy do Sienge MCP no Railway

## ⚡ Deploy Rápido

1. **Fork/Clone** este repositório
2. **Conecte ao Railway**: https://railway.app
3. **Configure as variáveis**:
   ```
   SIENGE_API_KEY=sua_api_key
   SIENGE_BASE_URL=https://api.sienge.com.br
   SIENGE_SUBDOMAIN=sua_empresa
   ```
4. **Deploy automático** 🎉

## 📖 Documentação Completa

👉 **[RAILWAY_DEPLOY.md](./RAILWAY_DEPLOY.md)** - Guia completo de deploy

## 🧪 Teste Local

```bash
# Configurar .env baseado no .env.example
cp .env.example .env
# Editar .env com suas credenciais

# Instalar dependências
pip install -r requirements.txt

# Testar localmente
python test_local.py
```

## 🔗 URLs Após Deploy

- **📚 Docs**: `https://seu-app.up.railway.app/docs`
- **🔧 API**: `https://seu-app.up.railway.app/mcp/tools/`
- **✅ Test**: `https://seu-app.up.railway.app/mcp/tools/test_sienge_connection/call`

---

**Feito com ❤️ pela ECBIESEK**