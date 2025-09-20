# Dockerfile para deploy do Sienge MCP no Railway
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema se necessário
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de dependências
COPY requirements.txt pyproject.toml app.py simple_server.py ./
COPY src/ ./src/

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar o pacote em modo de desenvolvimento
RUN pip install -e .

# Expor a porta que o Railway irá usar
EXPOSE $PORT

# Criar usuário não-root para segurança
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

# Comando para iniciar o servidor
# O Railway define automaticamente a variável PORT
CMD ["python", "simple_server.py"]