#!/usr/bin/env powershell
<#
.SYNOPSIS
    Setup automatizado do Sienge MCP Server
.DESCRIPTION
    Este script automatiza completamente a instalação e configuração do Sienge MCP:
    - Verifica requisitos do sistema
    - Cria ambiente virtual Python
    - Instala dependências
    - Configura arquivos de ambiente
    - Configura Claude Desktop
    - Executa testes básicos
.NOTES
    Execução: .\setup.ps1
    Requisitos: Python 3.9+ e Claude Desktop instalados
#>

param(
    [switch]$SkipTests = $false,
    [switch]$Force = $false
)

# Configurações
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$VENV_DIR = Join-Path $SCRIPT_DIR ".venv"
$ENV_FILE = Join-Path $SCRIPT_DIR ".env"
$CLAUDE_CONFIG_DIR = "$env:APPDATA\Claude"
$CLAUDE_CONFIG_FILE = "$CLAUDE_CONFIG_DIR\claude_desktop_config.json"

Write-Host "🚀 SIENGE MCP - SETUP AUTOMATIZADO" -ForegroundColor Green
Write-Host "=" * 50
Write-Host "📁 Diretório: $SCRIPT_DIR"
Write-Host ""

# Função para verificar se comando existe
function Test-Command {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Função para obter input do usuário com valor padrão
function Get-UserInput {
    param(
        [string]$Prompt,
        [string]$Default = "",
        [switch]$Secure = $false
    )
    
    if ($Default) {
        $fullPrompt = "$Prompt [$Default]: "
    } else {
        $fullPrompt = "$Prompt: "
    }
    
    if ($Secure) {
        $input = Read-Host $fullPrompt -AsSecureString
        $input = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($input))
    } else {
        $input = Read-Host $fullPrompt
    }
    
    if ([string]::IsNullOrWhiteSpace($input) -and $Default) {
        return $Default
    }
    return $input
}

# 1. VERIFICAR REQUISITOS
Write-Host "🔍 1. VERIFICANDO REQUISITOS DO SISTEMA" -ForegroundColor Cyan
Write-Host "-" * 40

# Verificar Python
if (-not (Test-Command "python")) {
    Write-Host "❌ Python não encontrado!" -ForegroundColor Red
    Write-Host "📥 Instale Python 3.9+ de: https://python.org/downloads/" -ForegroundColor Yellow
    Write-Host "✅ Certifique-se de marcar 'Add Python to PATH' durante a instalação" -ForegroundColor Yellow
    exit 1
}

$pythonVersion = python --version 2>&1
Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green

# Verificar versão do Python
try {
    $versionOutput = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    $majorMinor = $versionOutput.Split('.')
    $major = [int]$majorMinor[0]
    $minor = [int]$majorMinor[1]
    
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 9)) {
        Write-Host "❌ Python 3.9+ é necessário. Versão atual: $versionOutput" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "⚠️ Não foi possível verificar a versão do Python" -ForegroundColor Yellow
}

# Verificar pip
if (-not (Test-Command "pip")) {
    Write-Host "❌ pip não encontrado!" -ForegroundColor Red
    Write-Host "📥 Instale pip ou reinstale Python com pip incluído" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ pip encontrado" -ForegroundColor Green

# Verificar Claude Desktop
$claudeDesktopPaths = @(
    "$env:LOCALAPPDATA\Programs\Claude\Claude.exe",
    "$env:PROGRAMFILES\Claude\Claude.exe",
    "$env:PROGRAMFILES(X86)\Claude\Claude.exe"
)

$claudeFound = $false
foreach ($path in $claudeDesktopPaths) {
    if (Test-Path $path) {
        $claudeFound = $true
        Write-Host "✅ Claude Desktop encontrado: $path" -ForegroundColor Green
        break
    }
}

if (-not $claudeFound) {
    Write-Host "⚠️ Claude Desktop não encontrado nos locais padrão" -ForegroundColor Yellow
    Write-Host "📥 Baixe de: https://claude.ai/download" -ForegroundColor Yellow
    Write-Host "ℹ️ Você pode continuar o setup e instalar o Claude depois" -ForegroundColor Cyan
    
    $continue = Read-Host "Continuar sem Claude Desktop? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
}

# 2. CRIAR AMBIENTE VIRTUAL
Write-Host "`n🐍 2. CONFIGURANDO AMBIENTE VIRTUAL PYTHON" -ForegroundColor Cyan
Write-Host "-" * 40

if (Test-Path $VENV_DIR) {
    if ($Force) {
        Write-Host "🗑️ Removendo ambiente virtual existente..." -ForegroundColor Yellow
        Remove-Item $VENV_DIR -Recurse -Force
    } else {
        Write-Host "✅ Ambiente virtual já existe: $VENV_DIR" -ForegroundColor Green
        $recreate = Read-Host "Recriar ambiente virtual? (y/N)"
        if ($recreate -eq "y" -or $recreate -eq "Y") {
            Write-Host "🗑️ Removendo ambiente virtual existente..." -ForegroundColor Yellow
            Remove-Item $VENV_DIR -Recurse -Force
        }
    }
}

if (-not (Test-Path $VENV_DIR)) {
    Write-Host "🔨 Criando ambiente virtual..." -ForegroundColor Yellow
    python -m venv $VENV_DIR
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Erro ao criar ambiente virtual" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Ambiente virtual criado" -ForegroundColor Green
}

# Ativar ambiente virtual
$activateScript = Join-Path $VENV_DIR "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "🔌 Ativando ambiente virtual..." -ForegroundColor Yellow
    & $activateScript
} else {
    Write-Host "❌ Script de ativação não encontrado: $activateScript" -ForegroundColor Red
    exit 1
}

# 3. INSTALAR DEPENDÊNCIAS
Write-Host "`n📦 3. INSTALANDO DEPENDÊNCIAS" -ForegroundColor Cyan
Write-Host "-" * 40

$requirementsFile = Join-Path $SCRIPT_DIR "requirements.txt"
if (Test-Path $requirementsFile) {
    Write-Host "📋 Instalando dependências do requirements.txt..." -ForegroundColor Yellow
    & (Join-Path $VENV_DIR "Scripts\pip.exe") install -r $requirementsFile --upgrade
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Erro ao instalar dependências" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Dependências instaladas com sucesso" -ForegroundColor Green
} else {
    Write-Host "⚠️ Arquivo requirements.txt não encontrado" -ForegroundColor Yellow
    Write-Host "📦 Instalando dependências manualmente..." -ForegroundColor Yellow
    & (Join-Path $VENV_DIR "Scripts\pip.exe") install fastmcp httpx pydantic python-dotenv
}

# 4. CONFIGURAR CREDENCIAIS
Write-Host "`n🔐 4. CONFIGURANDO CREDENCIAIS SIENGE" -ForegroundColor Cyan
Write-Host "-" * 40

$configureCredentials = $true
if (Test-Path $ENV_FILE) {
    Write-Host "⚠️ Arquivo .env já existe" -ForegroundColor Yellow
    $overwrite = Read-Host "Reconfigurar credenciais? (y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        $configureCredentials = $false
        Write-Host "✅ Mantendo configurações existentes" -ForegroundColor Green
    }
}

if ($configureCredentials) {
    Write-Host "📝 Configure suas credenciais do Sienge:" -ForegroundColor Yellow
    Write-Host ""
    
    # Solicitar dados do usuário
    $baseUrl = Get-UserInput "URL base da API Sienge" "https://api.sienge.com.br"
    $subdomain = Get-UserInput "Subdomínio da sua empresa"
    $username = Get-UserInput "Nome de usuário"
    $password = Get-UserInput "Senha" -Secure
    $timeout = Get-UserInput "Timeout (segundos)" "30"
    
    # Validar dados obrigatórios
    if ([string]::IsNullOrWhiteSpace($subdomain)) {
        Write-Host "❌ Subdomínio é obrigatório!" -ForegroundColor Red
        exit 1
    }
    
    if ([string]::IsNullOrWhiteSpace($username)) {
        Write-Host "❌ Nome de usuário é obrigatório!" -ForegroundColor Red
        exit 1
    }
    
    if ([string]::IsNullOrWhiteSpace($password)) {
        Write-Host "❌ Senha é obrigatória!" -ForegroundColor Red
        exit 1
    }
    
    # Criar arquivo .env
    $envContent = @"
# Configurações da API Sienge
SIENGE_BASE_URL=$baseUrl
SIENGE_SUBDOMAIN=$subdomain
SIENGE_USERNAME=$username
SIENGE_PASSWORD=$password
SIENGE_TIMEOUT=$timeout

# Opcional: Use API Key em vez de username/password se disponível
# SIENGE_API_KEY=sua_api_key_aqui
"@
    
    Set-Content -Path $ENV_FILE -Value $envContent -Encoding UTF8
    Write-Host "✅ Arquivo .env criado com sucesso" -ForegroundColor Green
}

# 5. CONFIGURAR CLAUDE DESKTOP
Write-Host "`n🤖 5. CONFIGURANDO CLAUDE DESKTOP" -ForegroundColor Cyan
Write-Host "-" * 40

# Criar diretório do Claude se não existir
if (-not (Test-Path $CLAUDE_CONFIG_DIR)) {
    Write-Host "📁 Criando diretório do Claude..." -ForegroundColor Yellow
    New-Item -Path $CLAUDE_CONFIG_DIR -ItemType Directory -Force | Out-Null
}

# Gerar configuração dinâmica PORTÁVEL
# Usar caminhos relativos e python do ambiente virtual
$pythonExe = Join-Path $VENV_DIR "Scripts\python.exe"
$siengeScript = Join-Path $SCRIPT_DIR "sienge.py"

# Ler configurações do .env para incluir na configuração do Claude
$envVars = @{}
if (Test-Path $ENV_FILE) {
    Get-Content $ENV_FILE | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') {
            $envVars[$matches[1].Trim()] = $matches[2].Trim()
        }
    }
}

# CONFIGURAÇÃO PORTÁVEL: Usar caminhos absolutos específicos do usuário
$claudeConfig = @{
    mcpServers = @{
        sienge = @{
            command = $pythonExe
            args = @($siengeScript)
            env = $envVars
        }
    }
}

Write-Host "📋 Configuração gerada:" -ForegroundColor Yellow
Write-Host "   🐍 Python: $pythonExe" -ForegroundColor White
Write-Host "   📄 Script: $siengeScript" -ForegroundColor White
Write-Host "   🔐 Variáveis: $($envVars.Count) configuradas" -ForegroundColor White

# Backup da configuração existente
if (Test-Path $CLAUDE_CONFIG_FILE) {
    $backupFile = "$CLAUDE_CONFIG_FILE.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "💾 Fazendo backup da configuração existente..." -ForegroundColor Yellow
    Copy-Item $CLAUDE_CONFIG_FILE $backupFile
    Write-Host "✅ Backup salvo: $backupFile" -ForegroundColor Green
}

# Salvar nova configuração
$claudeConfigJson = $claudeConfig | ConvertTo-Json -Depth 10
Set-Content -Path $CLAUDE_CONFIG_FILE -Value $claudeConfigJson -Encoding UTF8
Write-Host "✅ Claude Desktop configurado: $CLAUDE_CONFIG_FILE" -ForegroundColor Green

# 6. EXECUTAR TESTES
if (-not $SkipTests) {
    Write-Host "`n🧪 6. EXECUTANDO TESTES BÁSICOS" -ForegroundColor Cyan
    Write-Host "-" * 40
    
    Write-Host "🔍 Testando importação de módulos..." -ForegroundColor Yellow
    $testResult = & $pythonExe -c "
try:
    import fastmcp, httpx, pydantic
    print('✅ Módulos importados com sucesso')
except ImportError as e:
    print(f'❌ Erro na importação: {e}')
    exit(1)
"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host $testResult -ForegroundColor Green
        
        Write-Host "🔌 Testando conexão com Sienge..." -ForegroundColor Yellow
        $diagnosticScript = Join-Path $SCRIPT_DIR "diagnostico_claude.py"
        if (Test-Path $diagnosticScript) {
            & $pythonExe $diagnosticScript
        } else {
            Write-Host "⚠️ Script de diagnóstico não encontrado" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Erro nos testes básicos" -ForegroundColor Red
    }
}

# 7. FINALIZAÇÃO
Write-Host "`n🎉 7. SETUP CONCLUÍDO!" -ForegroundColor Green
Write-Host "=" * 50
Write-Host ""
Write-Host "✅ Ambiente virtual criado: $VENV_DIR" -ForegroundColor Green
Write-Host "✅ Dependências instaladas" -ForegroundColor Green
Write-Host "✅ Credenciais configuradas: $ENV_FILE" -ForegroundColor Green
Write-Host "✅ Claude Desktop configurado: $CLAUDE_CONFIG_FILE" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 PRÓXIMOS PASSOS:" -ForegroundColor Cyan
Write-Host "1. Reinicie o Claude Desktop completamente (feche e abra)" -ForegroundColor White
Write-Host "2. Verifique se o servidor 'sienge' aparece na lista de MCPs" -ForegroundColor White
Write-Host "3. Teste com: 'Teste a conexão com a API Sienge'" -ForegroundColor White
Write-Host ""
Write-Host "📚 COMANDOS ÚTEIS:" -ForegroundColor Cyan
Write-Host "- Ativar ambiente: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "- Executar diagnóstico: python diagnostico_claude.py" -ForegroundColor White
Write-Host "- Reconfigurar: .\setup.ps1 -Force" -ForegroundColor White
Write-Host ""
Write-Host "❓ Problemas? Consulte o README.md ou execute o diagnóstico" -ForegroundColor Yellow
