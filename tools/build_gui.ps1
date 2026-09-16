[CmdletBinding()]
param([string]$Python = 'python')

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$pythonPath = (Get-Command $Python -CommandType Application | Select-Object -First 1).Source
$projectRoot = Split-Path -Parent $PSScriptRoot
$originalPath = $env:PATH
Push-Location -LiteralPath $projectRoot
try {
    $pythonBase = & $pythonPath -c 'import sys; print(sys.base_prefix)'
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo identificar el interprete de compilacion.' }
    # Do not collect DLLs from unrelated tools on PATH (for example Poppler ICU).
    # Keep Python/Conda support directories and prefer Windows system libraries.
    $buildPath = @(
        (Split-Path -Parent $pythonPath),
        (Join-Path $env:SystemRoot 'System32'),
        $env:SystemRoot,
        $pythonBase,
        (Join-Path $pythonBase 'Library\bin')
    ) | Where-Object { Test-Path -LiteralPath $_ }
    $env:PATH = $buildPath -join ';'
    & $pythonPath -m PyInstaller --clean --noconfirm AutomatizacionUsuarios.spec
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller no pudo completar el build.' }

    $distribution = Join-Path $projectRoot 'dist\AutomatizacionUsuarios'
    Copy-Item -LiteralPath (Join-Path $projectRoot '.env.example') -Destination $distribution
    # A unique report prevents a previous successful smoke check from hiding a failure.
    $report = Join-Path $projectRoot ('build\gui-self-check-' + [guid]::NewGuid().ToString('N') + '.json')
    $executable = Join-Path $distribution 'AutomatizacionUsuarios.exe'
    $process = Start-Process -FilePath $executable -ArgumentList @('--self-check', ('"' + $report + '"')) -WorkingDirectory $env:TEMP -WindowStyle Hidden -PassThru
    if (-not $process.WaitForExit(60000)) {
        $process.Kill()
        throw 'El self-check del ejecutable excedio 60 segundos.'
    }
    $process.Refresh()
    if ($process.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $report)) {
        throw "Fallo el self-check del ejecutable. Revisa: $report"
    }
    $result = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
    if (-not $result.ok) { throw "Self-check incompleto: $report" }
    Write-Host "Build verificado: $executable"
    Write-Host "Reporte: $report"
    Write-Host 'Distribuye toda la carpeta. Configura .env por separado a partir de .env.example.'
}
finally {
    $env:PATH = $originalPath
    Pop-Location
}
