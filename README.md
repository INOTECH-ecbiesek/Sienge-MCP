# Sienge MCP Server

Um servidor Model Context Protocol (MCP) para integração com a API do Sienge, sistema de gestão para empresas de construção civil.

## 🚀 Funcionalidades

### 📊 Contas a Receber
- **get_sienge_accounts_receivable**: Lista contas a receber com filtros por período
- Utiliza a Bulk-data API do Sienge para consultas eficientes
- Suporte a filtros por data de vencimento e data de competência

### 🏢 Projetos e Empresas
- **get_sienge_projects**: Lista todos os projetos/empresas disponíveis
- Informações detalhadas incluindo ID, nome, endereço e status

### 📝 Notas Fiscais de Compra
- **get_sienge_purchase_invoices**: Lista todas as notas fiscais de compra
- **get_sienge_purchase_invoice_details**: Detalhes completos de uma nota fiscal específica
- **get_sienge_purchase_invoice_items**: Lista itens de uma nota fiscal
- **get_sienge_purchase_invoice_payments**: Lista pagamentos de uma nota fiscal
- **search_sienge_purchase_invoices**: Busca avançada com múltiplos filtros

### 🔍 Solicitações de Compra
- **get_sienge_purchase_requests**: Lista solicitações de compra do sistema

## 📦 Instalação

### Via PyPI (Recomendado)
```bash
pip install sienge-ecbiesek-mcp
```

### Via Código Fonte
```bash
git clone https://github.com/INOTECH-ecbiesek/Sienge-MCP.git
cd Sienge-MCP
pip install -e .
```

## ⚙️ Configuração

### 1. Variáveis de Ambiente
Crie um arquivo `.env` no diretório do projeto com as seguintes variáveis:

```env
# Configurações da API do Sienge
SIENGE_BASE_URL=https://api.sienge.com.br
SIENGE_SUBDOMAIN=seu_subdominio
SIENGE_USERNAME=seu_usuario
SIENGE_PASSWORD=sua_senha
SIENGE_TIMEOUT=30
```

### 2. Configuração no Claude Desktop

#### Configuração Básica
Adicione ao seu arquivo de configuração do Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "sienge-mcp": {
      "command": "python",
      "args": ["-m", "sienge_mcp"],
      "env": {
        "SIENGE_BASE_URL": "https://api.sienge.com.br",
        "SIENGE_SUBDOMAIN": "seu_subdominio",
        "SIENGE_USERNAME": "seu_usuario",
        "SIENGE_PASSWORD": "sua_senha",
        "SIENGE_TIMEOUT": "30"
      }
    }
  }
}
```

#### Configuração com Virtual Environment
Se você estiver usando um ambiente virtual:

```json
{
  "mcpServers": {
    "sienge-mcp": {
      "command": "C:/caminho/para/seu/venv/Scripts/python.exe",
      "args": ["-m", "sienge_mcp"],
      "env": {
        "SIENGE_BASE_URL": "https://api.sienge.com.br",
        "SIENGE_SUBDOMAIN": "seu_subdominio",
        "SIENGE_USERNAME": "seu_usuario",
        "SIENGE_PASSWORD": "sua_senha",
        "SIENGE_TIMEOUT": "30"
      }
    }
  }
}
```

## 🔐 Autenticação

### Credenciais do Sienge
A autenticação é feita através de **usuário e senha** do Sienge, não por token API:

1. **SIENGE_BASE_URL**: URL base da API (`https://api.sienge.com.br`)
2. **SIENGE_SUBDOMAIN**: Seu subdomínio no Sienge (ex: `suaempresa`)
3. **SIENGE_USERNAME**: Seu nome de usuário no Sienge
4. **SIENGE_PASSWORD**: Sua senha no Sienge
5. **SIENGE_TIMEOUT**: Timeout das requisições em segundos (padrão: 30)

### URLs da API
- **API Base**: `https://api.sienge.com.br`
- **Endpoints v1**: `/sienge/api/public/v1/`
- **Bulk-data API**: `/bulk-data/`

## 💻 Como Usar

### 1. Iniciando o Servidor
```bash
# Via módulo Python
python -m sienge_mcp

# Ou diretamente
sienge-mcp-server
```

### 2. No Claude Desktop
Após configurar o servidor, reinicie o Claude Desktop. O servidor MCP será automaticamente carregado e as ferramentas ficarão disponíveis.

### 3. Exemplos de Uso no Claude

#### Consultar Contas a Receber
```
"Liste as contas a receber com vencimento entre 01/01/2024 e 31/01/2024"
```

#### Buscar Projetos
```
"Mostre todos os projetos disponíveis no Sienge"
```

#### Consultar Notas Fiscais
```
"Liste as notas fiscais de compra do mês atual"
```

#### Busca Avançada de Notas Fiscais
```
"Busque notas fiscais de compra com valor acima de R$ 10.000,00 emitidas em dezembro de 2023"
```

## 🛠️ Desenvolvimento

### Estrutura do Projeto
```
src/
├── sienge_mcp/
│   ├── __init__.py
│   ├── server.py          # Servidor MCP principal
│   ├── services/          # Serviços de integração
│   ├── tools/             # Ferramentas MCP
│   └── utils/
│       └── logger.py      # Sistema de logging
```

### Executando em Modo de Desenvolvimento
```bash
# Clone o repositório
git clone https://github.com/INOTECH-ecbiesek/Sienge-MCP.git
cd Sienge-MCP

# Crie um ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Instale as dependências
pip install -e .

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações

# Execute o servidor
python -m sienge_mcp
```

### Testando Localmente
```bash
# Instale as dependências de teste
pip install pytest pytest-asyncio

# Execute os testes
pytest tests/
```

## 📋 Requisitos

### Dependências
- Python >= 3.8
- fastmcp >= 2.12.3
- httpx >= 0.25.0
- pydantic >= 2.0.0
- python-dotenv >= 1.0.0

### Compatibilidade
- ✅ Windows
- ✅ macOS  
- ✅ Linux
- ✅ Claude Desktop
- ✅ Outros clientes MCP

## 🔧 Configurações Avançadas

### Logs e Debug
O servidor inclui sistema de logging configurável:

```python
# Nível de log via variável de ambiente
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### Timeout de Requisições
Configure o timeout das requisições HTTP:

```python
# Timeout em segundos (padrão: 30s)
SIENGE_TIMEOUT=60
```

### Cache de Respostas
Para melhor performance em consultas frequentes:

```python
# Habilitar cache (padrão: False)
SIENGE_CACHE_ENABLED=true
SIENGE_CACHE_TTL=300  # TTL em segundos
```

## 🚨 Solução de Problemas

### Erros Comuns

#### Erro 401 - Unauthorized
```
Causa: Credenciais inválidas (usuário/senha incorretos)
Solução: Verifique seu usuário e senha no Sienge
```

#### Erro 404 - Not Found
```
Causa: Endpoint incorreto ou recurso não encontrado
Solução: Verifique as URLs base da API
```

#### Erro 429 - Rate Limited
```
Causa: Muitas requisições por minuto
Solução: Implemente delay entre requisições
```

#### Servidor MCP não conecta
```
1. Verifique se o Python está no PATH
2. Confirme se o módulo está instalado: pip show sienge-ecbiesek-mcp
3. Teste a execução manual: python -m sienge_mcp
4. Verifique os logs do Claude Desktop
```

### Debug
Para debugar problemas de conexão:

```bash
# Execute com logs detalhados
LOG_LEVEL=DEBUG python -m sienge_mcp

# Teste a conectividade com a API
# Use as credenciais do seu arquivo de configuração para testar
```

## 📚 Documentação da API

### Endpoints Utilizados

#### API Padrão (v1)
- `GET /enterprises` - Lista empresas/projetos
- `GET /purchase-requests` - Solicitações de compra  
- `GET /purchase-invoices` - Notas fiscais de compra
- `GET /purchase-invoices/{id}` - Detalhes da nota fiscal
- `GET /purchase-invoices/{id}/items` - Itens da nota fiscal
- `GET /purchase-invoices/{id}/payments` - Pagamentos da nota fiscal

#### Bulk-data API
- `POST /income` - Contas a receber (bulk)

### Formatos de Data
- **ISO 8601**: `2024-01-01T00:00:00Z`
- **Brasileiro**: `01/01/2024`
- **Filtros de período**: `start_date` e `end_date`

### Códigos de Status
- `200` - Sucesso
- `400` - Requisição inválida
- `401` - Não autorizado
- `404` - Recurso não encontrado
- `429` - Rate limit excedido
- `500` - Erro interno do servidor

## 📄 Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🤝 Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/INOTECH-ecbiesek/Sienge-MCP/issues)
- **Documentação**: [Wiki do Projeto](https://github.com/INOTECH-ecbiesek/Sienge-MCP/wiki)
- **API Sienge**: [Documentação Oficial](https://api.sienge.com.br/docs)

## 📈 Versões

### v1.1.0 (Atual)
- ✅ Adicionadas 5 ferramentas para Notas Fiscais de Compra
- ✅ Suporte à Bulk-data API para contas a receber
- ✅ Correção de endpoints para projetos/empresas
- ✅ Melhorias na documentação e tratamento de erros

### v1.0.0
- ✅ Versão inicial com ferramentas básicas
- ✅ Integração com API padrão do Sienge
- ✅ Suporte a contas a receber, projetos e solicitações de compra

---

**Desenvolvido por INOTECH-ecbiesek** 🚀