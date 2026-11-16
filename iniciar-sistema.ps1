# Inicia la misma aplicación con la base configurada o con una copia sintética explícita.
param(
    [string]$CarpetaDemo2026,
    [string]$RaizDependencias = $PSScriptRoot
)
$ErrorActionPreference = 'Stop'
$raiz = $PSScriptRoot
$backend = Join-Path $raiz 'backend'
$frontend = Join-Path $raiz 'frontend'
$python = Join-Path (Join-Path $RaizDependencias 'backend') '.venv\Scripts\python.exe'
$vite = Join-Path $frontend 'node_modules\vite\bin\vite.js'
$urlApi = 'http://127.0.0.1:8000/api/v1'
# La misma precedencia de archivos que Vite en modo desarrollo.
foreach ($archivoEntorno in @('.env', '.env.local', '.env.development', '.env.development.local')) {
    $rutaEntorno = Join-Path $frontend $archivoEntorno
    if (Test-Path -LiteralPath $rutaEntorno) {
        foreach ($lineaEntorno in Get-Content -LiteralPath $rutaEntorno) {
            if ($lineaEntorno -match '^\s*VITE_API_BASE_URL\s*=\s*(.+?)\s*$') {
                $urlApi = $Matches[1].Trim().Trim('"').Trim("'")
            }
        }
    }
}
if ($env:VITE_API_BASE_URL) { $urlApi = $env:VITE_API_BASE_URL }
$usarDemo = [bool]$CarpetaDemo2026
$entornoDemo = @{}
if ($usarDemo) {
    $carpeta = (Get-Item -LiteralPath $CarpetaDemo2026).FullName
    $base = Join-Path $carpeta 'demo-2026.sqlite3'
    $modelos = Join-Path $carpeta 'modelos'
    if (-not (Test-Path -LiteralPath $base -PathType Leaf) -or
        -not (Get-ChildItem -LiteralPath $modelos -Filter '*.joblib' -File -ErrorAction SilentlyContinue)) {
        throw 'La carpeta de demostración debe contener demo-2026.sqlite3 y el archivo de modelo en modelos.'
    }
    $urlApi = 'http://127.0.0.1:8000/api/v1'
    $entornoDemo = @{
        DATABASE_URL = 'sqlite:///' + $base.Replace('', '/')
        RUTA_MODELOS_OPERATIVOS = $modelos
        DATOS_OPERATIVOS_SIMULADOS = 'true'
        ENVIRONMENT = 'development'
        JWT_SECRET_KEY = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
        BACKEND_CORS_ORIGINS = '["http://localhost:5173","http://127.0.0.1:5173"]'
        VITE_API_BASE_URL = $urlApi
    }
}
$direccionApi = $null
if (-not [Uri]::TryCreate($urlApi, [UriKind]::Absolute, [ref]$direccionApi) -or
    $direccionApi.Scheme -ne 'http' -or $direccionApi.Host -notin @('localhost', '127.0.0.1')) {
    throw 'El inicio local requiere VITE_API_BASE_URL con una dirección HTTP de localhost o 127.0.0.1.'
}
$puertoApi = $direccionApi.Port

if (-not (Test-Path -LiteralPath $python)) {
    throw 'Falta backend\.venv. Instala las dependencias del backend antes de iniciar.'
}
if (-not (Test-Path -LiteralPath $vite)) {
    throw 'Faltan las dependencias del frontend. Ejecuta npm ci en frontend.'
}
if (-not $usarDemo -and -not (Test-Path -LiteralPath (Join-Path $backend '.env'))) {
    throw 'Falta backend\.env.'
}
if (-not $usarDemo -and -not (Get-NetTCPConnection -State Listen -LocalPort 5432 -ErrorAction SilentlyContinue)) {
    throw 'PostgreSQL no está escuchando en el puerto 5432. Inícialo y vuelve a ejecutar este archivo.'
}

$node = (Get-Command node.exe -ErrorAction Stop).Source
$registro = Join-Path $env:TEMP 'sistema-activos-logs'
New-Item -ItemType Directory -Path $registro -Force | Out-Null
$marca = Get-Date -Format 'yyyyMMdd-HHmmss'

$apiEnUso = Get-NetTCPConnection -State Listen -LocalPort $puertoApi -ErrorAction SilentlyContinue
$webEnUso = Get-NetTCPConnection -State Listen -LocalPort 5173 -ErrorAction SilentlyContinue
if ($apiEnUso) {
    try {
        $estado = Invoke-RestMethod -Uri "http://127.0.0.1:$puertoApi/health" -TimeoutSec 3
    } catch {
        throw "El puerto $puertoApi está ocupado por otro servicio. Libéralo antes de iniciar."
    }
    if ([bool]$estado.datos_operativos_simulados -ne $usarDemo) {
        throw "El sistema ya está iniciado con otro conjunto de datos. Detén esa sesión antes de cambiar de modo."
    }
}
if ($usarDemo -and $webEnUso -and -not $apiEnUso) {
    throw 'La interfaz ya está iniciada. Cierra esa sesión antes de abrir la demostración.'
}

# Los procesos hijo reciben el perfil elegido; la terminal recupera sus variables originales.
$entornoAnterior = @{}
foreach ($clave in $entornoDemo.Keys) {
    $entornoAnterior[$clave] = [Environment]::GetEnvironmentVariable($clave, 'Process')
    [Environment]::SetEnvironmentVariable($clave, $entornoDemo[$clave], 'Process')
}
try {
    if (-not $apiEnUso) {
        $api = Start-Process -FilePath $python -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', [string]$puertoApi) -WorkingDirectory $backend -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $registro "backend-$marca.log") -RedirectStandardError (Join-Path $registro "backend-$marca.err.log")
        Write-Host "API iniciada (PID $($api.Id))."
    } else {
        Write-Host "El puerto $puertoApi ya está ocupado. Se comprobará la conexión configurada."
    }

    if (-not $webEnUso) {
        $web = Start-Process -FilePath $node -ArgumentList @('node_modules/vite/bin/vite.js', '--host', 'localhost', '--port', '5173', '--strictPort') -WorkingDirectory $frontend -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $registro "frontend-$marca.log") -RedirectStandardError (Join-Path $registro "frontend-$marca.err.log")
        Write-Host "Interfaz iniciada (PID $($web.Id))."
    } else {
        Write-Host 'El puerto 5173 ya está ocupado. Revisa si la interfaz ya está iniciada.'
    }

} finally {
    foreach ($clave in $entornoAnterior.Keys) {
        [Environment]::SetEnvironmentVariable($clave, $entornoAnterior[$clave], 'Process')
    }
}

$lista = @(
    @{ Nombre = 'API y conexión a la base'; Url = "http://127.0.0.1:$puertoApi/health/ready" },
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
