# CHANGELOG - Sienge MCP Server

## v1.2.1 (2024-12-19)
### 🔧 BUGFIX CRÍTICO
- **RESOLVIDO**: Erro "Unexpected keyword argument '_meta'" causado pelo MCP client
- **CORREÇÃO**: Adicionado parâmetro `_meta: Optional[Dict] = None` em todas as 50+ funções @mcp.tool
- **MOTIVO**: O runtime MCP envia automaticamente dados de metadata (userAgent, locale) que o servidor precisa aceitar
- **IMPACTO**: Todas as chamadas MCP agora funcionam sem erros de validação do Pydantic

### 📋 Detalhes Técnicos
- Aplicação automática via script Python em todas as funções decoradas
- Correção de sintaxe (vírgulas faltantes) após modificação em massa
- Validação completa da sintaxe e importação do módulo
- Mantida compatibilidade com versões anteriores (_meta é opcional)

## v1.2.0 (2024-12-19) 
### ✨ MELHORIAS PRINCIPAIS
- **7 CORREÇÕES PRIORITÁRIAS**: Cache, bulk polling, JSON normalization, pagination, query parameters, observabilidade, aliases
- **50+ FERRAMENTAS**: Conjunto completo de ferramentas para integração Sienge
- **ARQUITETURA MELHORADA**: Separação entre camada MCP e camada de serviços
- **PUBLICAÇÃO PYPI**: Disponível em https://pypi.org/project/sienge-ecbiesek-mcp/

### 🎯 Funcionalidades Principais
- Autenticação flexível (Bearer Token + Basic Auth)
- Cache inteligente com expiração
- Polling assíncrono para bulk-data
- Normalização automática de parâmetros
- Paginação otimizada
- Observabilidade com X-Request-ID
- Alias compatíveis com checklist existente

## v1.1.5 e anteriores
- Versões de desenvolvimento e correções incrementais
- Base inicial do servidor MCP FastMCP
- Integração básica com API Sienge