# 🚀 Guia de Deploy do Sienge MCP no Railway

Este guia te ajudará a fazer o deploy do servidor Sienge MCP no Railway para que você possa acessá-lo através de um link HTTP.

## 📋 Pré-requisitos

- Conta no [Railway](https://railway.app)
- Conta no GitHub com o código do projeto
- Credenciais de acesso à API do Sienge

## 🛠️ Passo a Passo

### 1. Preparar o Repositório

Certifique-se de que o projeto está no GitHub com todos os arquivos necessários:
- `Dockerfile`
- `railway.json`
- `app.py`
- `.env.example`
- `src/sienge_mcp/server.py`
- `requirements.txt`
- `pyproject.toml`

### 2. Fazer Deploy no Railway

1. **Acesse o Railway**: https://railway.app
2. **Faça login** com sua conta GitHub
3. **Clique em "New Project"**
4. **Selecione "Deploy from GitHub repo"**
5. **Escolha o repositório** do Sienge-MCP
6. **Aguarde o build automático**

### 3. Configurar Variáveis de Ambiente

No dashboard do Railway, vá na aba **"Variables"** e configure:

#### 🔑 Credenciais do Sienge (Escolha um método)

**Opção 1 - API Key (Recomendado):**
```
SIENGE_API_KEY=sua_api_key_aqui
SIENGE_BASE_URL=https://api.sienge.com.br
SIENGE_SUBDOMAIN=sua_empresa
```

**Opção 2 - Basic Auth:**
```
SIENGE_USERNAME=seu_usuario
SIENGE_PASSWORD=sua_senha
SIENGE_BASE_URL=https://api.sienge.com.br
SIENGE_SUBDOMAIN=sua_empresa
```

#### ⚙️ Configurações Opcionais:
```
REQUEST_TIMEOUT=30
ENVIRONMENT=production
```

### 4. Verificar o Deploy

1. **Aguarde o deploy** completar (pode levar 2-5 minutos)
2. **Acesse a URL** fornecida pelo Railway (algo como `https://seu-projeto.up.railway.app`)
3. **Teste os endpoints**:
   - Documentação: `https://seu-projeto.up.railway.app/docs`
   - Teste de conexão: `https://seu-projeto.up.railway.app/mcp/tools/test_sienge_connection/call`

## 🔗 URLs Importantes

Após o deploy, você terá acesso a:

- **📚 Documentação Interativa**: `https://seu-projeto.up.railway.app/docs`
- **🔧 API REST**: `https://seu-projeto.up.railway.app/mcp/tools/`
- **❤️ Health Check**: `https://seu-projeto.up.railway.app/docs`

## 🧪 Como Testar

### 1. Testar Conexão com Sienge
```bash
curl -X POST "https://seu-projeto.up.railway.app/mcp/tools/test_sienge_connection/call"
```

### 2. Buscar Clientes
```bash
curl -X POST "https://seu-projeto.up.railway.app/mcp/tools/get_sienge_customers/call" \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"limit": 10}}'
```

### 3. Buscar Contas a Receber
```bash
curl -X POST "https://seu-projeto.up.railway.app/mcp/tools/get_sienge_accounts_receivable/call" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "start_date": "2024-01-01",
      "end_date": "2024-12-31"
    }
  }'
```

## 🔧 Ferramentas Disponíveis

O servidor expõe 20+ ferramentas da API Sienge:

### 🏗️ Conexão e Teste
- `test_sienge_connection` - Testa conexão com a API

### 👥 Clientes
- `get_sienge_customers` - Buscar clientes
- `get_sienge_customer_types` - Tipos de clientes

### 💰 Financeiro
- `get_sienge_accounts_receivable` - Contas a receber
- `get_sienge_accounts_receivable_by_bills` - Por títulos
- `get_sienge_bills` - Títulos a pagar

### 🛒 Compras
- `get_sienge_purchase_orders` - Pedidos de compra
- `get_sienge_purchase_requests` - Solicitações de compra
- `create_sienge_purchase_request` - Criar solicitação

### 📄 Notas Fiscais
- `get_sienge_purchase_invoice` - Buscar nota fiscal
- `create_sienge_purchase_invoice` - Criar nota fiscal
- `add_items_to_purchase_invoice` - Adicionar itens

### 🏢 Projetos/Obras
- `get_sienge_projects` - Buscar empreendimentos
- `get_sienge_enterprise_by_id` - Por ID específico

### 📦 Estoque
- `get_sienge_stock_inventory` - Inventário
- `get_sienge_stock_reservations` - Reservas

## ⚠️ Troubleshooting

### Deploy Falhou?
1. Verifique os logs no dashboard do Railway
2. Confirme que o `Dockerfile` está correto
3. Verifique se as dependências estão no `requirements.txt`

### API não responde?
1. Verifique as variáveis de ambiente
2. Teste a conexão: `/mcp/tools/test_sienge_connection/call`
3. Confirme suas credenciais do Sienge

### Erro de autenticação?
1. Confirme `SIENGE_API_KEY` ou `SIENGE_USERNAME/PASSWORD`
2. Verifique o `SIENGE_SUBDOMAIN`
3. Teste as credenciais diretamente na API do Sienge

## 📱 Usando com Claude

Depois do deploy, você pode usar o servidor com Claude configurando:

```json
{
  "mcpServers": {
    "sienge": {
      "command": "uv",
      "args": [
        "tool",
        "run",
        "mcp-client-sse",
        "https://seu-projeto.up.railway.app/mcp/sse"
      ]
    }
  }
}
```

## 💡 Dicas

1. **Use HTTPS**: Railway fornece automaticamente
2. **Monitore logs**: Dashboard Railway tem logs em tempo real  
3. **Backup das variáveis**: Anote suas configurações
4. **Teste regularmente**: Use endpoint de health check
5. **Domínio customizado**: Railway permite configurar domínio próprio

## 📞 Suporte

- **GitHub Issues**: [INOTECH-ecbiesek/Sienge-MCP](https://github.com/INOTECH-ecbiesek/Sienge-MCP)
- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **Sienge API**: [api.sienge.com.br](https://api.sienge.com.br)

---

✅ **Pronto!** Seu servidor Sienge MCP está rodando no Railway e acessível via HTTP!