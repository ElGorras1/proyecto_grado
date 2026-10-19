# Inicia el sistema instalado localmente. No crea ni modifica la base de datos.
$ErrorActionPreference = 'Stop'
$raiz = $PSScriptRoot
$backend = Join-Path $raiz 'backend'
$frontend = Join-Path $raiz 'frontend'
$python = Join-Path $backend '.venv\Scripts\python.exe'
$vite = Join-Path $frontend 'node_modules\vite\bin\vite.js'

if (-not (Test-Path -LiteralPath $python)) {
    throw 'Falta backend\.venv. Instala las dependencias del backend antes de iniciar.'
}
if (-not (Test-Path -LiteralPath $vite)) {
    throw 'Faltan las dependencias del frontend. Ejecuta npm ci en frontend.'
}
if (-not (Test-Path -LiteralPath (Join-Path $backend '.env'))) {
    throw 'Falta backend\.env.'
}
if (-not (Get-NetTCPConnection -State Listen -LocalPort 5432 -ErrorAction SilentlyContinue)) {
    throw 'PostgreSQL no está escuchando en el puerto 5432. Inícialo y vuelve a ejecutar este archivo.'
}

$node = (Get-Command node.exe -ErrorAction Stop).Source
$registro = Join-Path $env:TEMP 'sistema-activos-logs'
New-Item -ItemType Directory -Path $registro -Force | Out-Null
$marca = Get-Date -Format 'yyyyMMdd-HHmmss'

if (-not (Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue)) {
    $api = Start-Process -FilePath $python -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000') -WorkingDirectory $backend -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $registro "backend-$marca.log") -RedirectStandardError (Join-Path $registro "backend-$marca.err.log")
    Write-Host "API iniciada (PID $($api.Id))."
} else {
    Write-Host 'El puerto 8000 ya está ocupado. Revisa si la API ya está iniciada.'
}

if (-not (Get-NetTCPConnection -State Listen -LocalPort 5173 -ErrorAction SilentlyContinue)) {
    $web = Start-Process -FilePath $node -ArgumentList @('node_modules/vite/bin/vite.js', '--host', 'localhost', '--port', '5173', '--strictPort') -WorkingDirectory $frontend -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $registro "frontend-$marca.log") -RedirectStandardError (Join-Path $registro "frontend-$marca.err.log")
    Write-Host "Interfaz iniciada (PID $($web.Id))."
} else {
    Write-Host 'El puerto 5173 ya está ocupado. Revisa si la interfaz ya está iniciada.'
}

$lista = @(
    @{ Nombre = 'API y conexión a la base'; Url = 'http://127.0.0.1:8000/health/ready' },
    @{ Nombre = 'Interfaz'; Url = 'http://localhost:5173/' }
)
foreach ($servicio in $lista) {
    $activo = $false
    for ($intento = 0; $intento -lt 60; $intento++) {
        try {
            $respuesta = Invoke-WebRequest -Uri $servicio.Url -TimeoutSec 2 -UseBasicParsing
            if ($respuesta.StatusCode -eq 200) { $activo = $true; break }
        } catch { Start-Sleep -Milliseconds 500 }
    }
    if ($activo) {
        Write-Host "$($servicio.Nombre) disponible: $($servicio.Url)"
    } else {
        Write-Warning "$($servicio.Nombre) no respondió. Revisa los registros en $registro"
    }
}
