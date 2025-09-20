# Script de Atualização Automatizada - Sienge ECBIESEK MCP
# Execute este script após fazer mudanças no código

param(
    [Parameter(Mandatory=$true)]
    [string]$NovaVersao
)

Write-Host "🔄 INICIANDO ATUALIZAÇÃO PARA VERSÃO $NovaVersao" -ForegroundColor Green

# 1. Atualizar versão no pyproject.toml
Write-Host "📝 Atualizando versão no pyproject.toml..." -ForegroundColor Yellow
$content = Get-Content "pyproject.toml" -Raw
$content = $content -replace 'version = "[^"]*"', "version = `"$NovaVersao`""
Set-Content "pyproject.toml" -Value $content -NoNewline

# 2. Limpar builds anteriores
Write-Host "🧹 Limpando builds anteriores..." -ForegroundColor Yellow
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "src\*.egg-info" -Recurse -Force -ErrorAction SilentlyContinue

# 3. Build nova versão
Write-Host "🏗️ Buildando nova versão..." -ForegroundColor Yellow
.\.venv\Scripts\python.exe -m build

# 4. Testar instalação local
Write-Host "🧪 Testando nova versão localmente..." -ForegroundColor Yellow
$wheelFile = Get-ChildItem -Path "dist\*.whl" | Select-Object -First 1
.\.venv\Scripts\python.exe -m pip install $wheelFile.FullName --force-reinstall

# 5. Verificar se comando funciona
Write-Host "✅ Verificando comando..." -ForegroundColor Yellow
$testResult = & .\.venv\Scripts\sienge-ecbiesek-mcp.exe --help 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Comando funcionando!" -ForegroundColor Green
} else {
    Write-Host "❌ Erro no comando! Verifique antes de publicar." -ForegroundColor Red
    exit 1
}

# 6. Publicar no PyPI
Write-Host "📤 Publicando no PyPI..." -ForegroundColor Yellow
.\.venv\Scripts\twine.exe upload $wheelFile.FullName

if ($LASTEXITCODE -eq 0) {
    Write-Host "🎉 ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!" -ForegroundColor Green
    Write-Host "🌐 Verifique em: https://pypi.org/project/sienge-ecbiesek-mcp/$NovaVersao/" -ForegroundColor Cyan
    Write-Host "📋 A equipe receberá a atualização automaticamente no próximo uso." -ForegroundColor Blue
} else {
    Write-Host "❌ Erro na publicação. Verifique suas credenciais PyPI." -ForegroundColor Red
}
