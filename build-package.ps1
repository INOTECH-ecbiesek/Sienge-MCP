#!/usr/bin/env powershell
<#
.SYNOPSIS
    Build e deploy do pacote Sienge MCP Server para PyPI
.DESCRIPTION
    Este script automatiza a construção e publicação do pacote Python
.NOTES
    Execução: .\build-package.ps1
    Requisitos: Python, pip, build, twine
#>

param(
    [switch]$TestPyPI = $false,
    [switch]$SkipBuild = $false,
    [switch]$SkipUpload = $false
)

Write-Host "🚀 SIENGE MCP - BUILD & DEPLOY" -ForegroundColor Green
Write-Host "=" * 40

# Verificar se estamos no diretório correto
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "❌ Arquivo pyproject.toml não encontrado!" -ForegroundColor Red
    Write-Host "Execute este script no diretório raiz do projeto" -ForegroundColor Yellow
    exit 1
}

if (-not $SkipBuild) {
    # 1. LIMPAR BUILDS ANTERIORES
    Write-Host "`n🧹 1. LIMPANDO BUILDS ANTERIORES" -ForegroundColor Cyan
    if (Test-Path "dist") {
        Remove-Item "dist" -Recurse -Force
        Write-Host "✅ Pasta dist removida" -ForegroundColor Green
    }
    if (Test-Path "build") {
        Remove-Item "build" -Recurse -Force
        Write-Host "✅ Pasta build removida" -ForegroundColor Green
    }
    if (Test-Path "src\sienge_mcp.egg-info") {
        Remove-Item "src\sienge_mcp.egg-info" -Recurse -Force
        Write-Host "✅ Pasta egg-info removida" -ForegroundColor Green
    }

    # 2. INSTALAR DEPENDÊNCIAS DE BUILD
    Write-Host "`n📦 2. INSTALANDO DEPENDÊNCIAS DE BUILD" -ForegroundColor Cyan
    pip install --upgrade pip build twine
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Erro ao instalar dependências de build" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Dependências instaladas" -ForegroundColor Green

    # 3. EXECUTAR TESTES (se existirem)
    Write-Host "`n🧪 3. EXECUTANDO TESTES" -ForegroundColor Cyan
    if (Test-Path "tests") {
        python -m pytest tests/ -v
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Testes falharam!" -ForegroundColor Red
            exit 1
        }
        Write-Host "✅ Todos os testes passaram" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Pasta tests não encontrada, pulando testes" -ForegroundColor Yellow
    }

    # 4. BUILD DO PACOTE
    Write-Host "`n🔨 4. CONSTRUINDO PACOTE" -ForegroundColor Cyan
    python -m build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Erro na construção do pacote" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Pacote construído com sucesso em dist/" -ForegroundColor Green

    # Listar arquivos gerados
    Write-Host "`n📋 Arquivos gerados:" -ForegroundColor Yellow
    Get-ChildItem "dist" | ForEach-Object {
        Write-Host "   📦 $($_.Name)" -ForegroundColor White
    }
}

if (-not $SkipUpload) {
    # 5. VERIFICAR PACOTE
    Write-Host "`n🔍 5. VERIFICANDO PACOTE" -ForegroundColor Cyan
    python -m twine check dist/*
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Verificação do pacote falhou" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Pacote verificado com sucesso" -ForegroundColor Green

    # 6. UPLOAD PARA PYPI
    Write-Host "`n🚀 6. FAZENDO UPLOAD PARA PYPI" -ForegroundColor Cyan
    
    if ($TestPyPI) {
        Write-Host "📤 Fazendo upload para TestPyPI..." -ForegroundColor Yellow
        python -m twine upload --repository testpypi dist/*
        $installCommand = "pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ sienge-mcp-server"
    } else {
        Write-Host "📤 Fazendo upload para PyPI..." -ForegroundColor Yellow
        Write-Host "⚠️ ATENÇÃO: Isso irá publicar no PyPI oficial!" -ForegroundColor Red
        $confirm = Read-Host "Continuar? (y/N)"
        if ($confirm -ne "y" -and $confirm -ne "Y") {
            Write-Host "❌ Upload cancelado pelo usuário" -ForegroundColor Yellow
            exit 0
        }
        
        python -m twine upload dist/*
        $installCommand = "pip install sienge-mcp-server"
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Erro no upload" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Upload realizado com sucesso!" -ForegroundColor Green
}

# 7. INSTRUÇÕES FINAIS
Write-Host "`n🎉 7. PACOTE PUBLICADO COM SUCESSO!" -ForegroundColor Green
Write-Host "=" * 40
Write-Host ""
Write-Host "📦 Para instalar o pacote:" -ForegroundColor Cyan
Write-Host "   $installCommand" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Para usar no Claude Desktop:" -ForegroundColor Cyan
Write-Host '   {' -ForegroundColor White
Write-Host '     "mcpServers": {' -ForegroundColor White
Write-Host '       "sienge": {' -ForegroundColor White
Write-Host '         "command": "sienge-mcp",' -ForegroundColor White
Write-Host '         "env": {' -ForegroundColor White
Write-Host '           "SIENGE_BASE_URL": "https://api.sienge.com.br",' -ForegroundColor White
Write-Host '           "SIENGE_SUBDOMAIN": "sua_empresa",' -ForegroundColor White
Write-Host '           "SIENGE_USERNAME": "seu_usuario",' -ForegroundColor White
Write-Host '           "SIENGE_PASSWORD": "sua_senha",' -ForegroundColor White
Write-Host '           "SIENGE_TIMEOUT": "30"' -ForegroundColor White
Write-Host '         }' -ForegroundColor White
Write-Host '       }' -ForegroundColor White
Write-Host '     }' -ForegroundColor White
Write-Host '   }' -ForegroundColor White
Write-Host ""
Write-Host "🚀 Agora qualquer pessoa pode usar apenas instalando o pacote!" -ForegroundColor Green
