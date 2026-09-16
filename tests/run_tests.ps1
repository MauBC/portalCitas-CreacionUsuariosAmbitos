[CmdletBinding()]
param(
    [ValidateSet('All', 'Local', 'Integration')]
    [string]$Suite = 'All',
    [string]$Python = 'python',
    [switch]$List
)

$ErrorActionPreference = 'Stop'
# Native failures are handled below using LASTEXITCODE, including on PowerShell 7.
$PSNativeCommandUseErrorActionPreference = $false
$projectRoot = Split-Path -Parent $PSScriptRoot

# Real-service tests run in order: Phase 1 prepares the scope tests' input.
$integrationTests = @(
    'test_01_sistema.py',
    'test_02_usuarios.py',
    'test_03_ambitos.py',
    'test_04_ambitos_final.py'
)

$tests = @(Get-ChildItem -LiteralPath $PSScriptRoot -Filter 'test_*.py' -File |
    Sort-Object Name |
    Where-Object {
        $isIntegration = $_.Name -in $integrationTests
        $Suite -eq 'All' -or
        ($Suite -eq 'Integration' -and $isIntegration) -or
        ($Suite -eq 'Local' -and -not $isIntegration)
    })

if ($tests.Count -eq 0) {
    throw "No se encontraron pruebas para la suite $Suite."
}

if ($List) {
    $tests | Select-Object Name, @{
        Name = 'Suite'
        Expression = {
            if ($_.Name -in $integrationTests) { 'Integration' } else { 'Local' }
        }
    }
    exit 0
}

# Resolve before changing directory so relative interpreter paths work.
# Windows PowerShell may return multiple applications; honor PATH precedence.
$pythonCommand = Get-Command -Name $Python -CommandType Application -ErrorAction Stop |
    Select-Object -First 1
$pythonPath = $pythonCommand.Source
$results = @()
$suiteExitCode = 0

Push-Location -LiteralPath $projectRoot
try {
    Write-Host "Suite: $Suite | Pruebas: $($tests.Count) | Python: $pythonPath"

    foreach ($test in $tests) {
        Write-Host "`nEjecutando: $($test.Name)"
        $timer = [System.Diagnostics.Stopwatch]::StartNew()
        & $pythonPath $test.FullName
        $testExitCode = $LASTEXITCODE
        $timer.Stop()

        $results += [PSCustomObject]@{
            Prueba = $test.Name
            Resultado = if ($testExitCode -eq 0) { 'OK' } else { 'ERROR' }
            Segundos = [Math]::Round($timer.Elapsed.TotalSeconds, 2)
        }

        if ($testExitCode -ne 0) {
            $suiteExitCode = $testExitCode
            Write-Host "Detenido: $($test.Name) fallo con codigo $testExitCode."
            break
        }
    }
}
finally {
    Pop-Location
}

$results | Format-Table -AutoSize | Out-Host
Write-Host "Ejecutadas: $($results.Count)/$($tests.Count)"
if ($suiteExitCode -eq 0) {
    Write-Host 'RESULTADO: OK'
} else {
    Write-Host 'RESULTADO: ERROR'
}
exit $suiteExitCode
