# Prepara el venv (solo la primera vez) y ejecuta el notebook completo de Proyecto3.
# Uso: powershell -NoProfile -ExecutionPolicy Bypass -File correr.ps1
Set-Location $PSScriptRoot
$py = ".venv\Scripts\python.exe"

function Paso([string]$nombre, [scriptblock]$bloque) {
    Write-Output "[p3] $nombre"
    & $bloque
    if ($LASTEXITCODE -ne 0) { throw "[p3] fallo: $nombre (codigo $LASTEXITCODE)" }
}

if (-not (Test-Path $py)) { Paso "crear venv" { python -m venv .venv } }
Paso "pip" { & $py -m pip install -q --upgrade pip }

# torch con CUDA antes que el resto, para que requirements.txt no traiga el de solo CPU.
& $py -c "import torch, sys; sys.exit(0 if torch.version.cuda else 1)" 2>$null
if ($LASTEXITCODE -ne 0) {
    Paso "torch cu128" { & $py -m pip install -q torch --index-url https://download.pytorch.org/whl/cu128 }
}
Paso "requirements" { & $py -m pip install -q -r requirements.txt }

& $py -c "import es_core_news_md" 2>$null
if ($LASTEXITCODE -ne 0) {
    Paso "spaCy es_core_news_md" { & $py -m pip install -q https://github.com/explosion/spacy-models/releases/download/es_core_news_md-3.8.0/es_core_news_md-3.8.0-py3-none-any.whl }
}
Paso "verificar CUDA" { & $py -c "import torch; assert torch.cuda.is_available(), 'sin CUDA'; print('torch', torch.__version__, 'cuda', torch.version.cuda, torch.cuda.get_device_name(0))" }

$inicio = Get-Date
Paso "ejecutar notebook" { & $py -m jupyter nbconvert --to notebook --execute Proyecto3_Sentiment_Analysis.ipynb --output ejecutado.ipynb --ExecutePreprocessor.timeout=-1 --ExecutePreprocessor.kernel_name=python3 }
Write-Output ("[p3] listo en {0:N1} min" -f ((Get-Date) - $inicio).TotalMinutes)
