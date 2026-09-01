$ErrorActionPreference = "Stop"

$tests = @(
    ".\test_01_sistema.py",
    ".\test_02_usuarios.py",
    ".\test_03_ambitos.py"
)

Write-Host ""
Write-Host "============================================================"
Write-Host " TEST SUITE - AUTOMATIZACION USUARIOS / AMBITOS"
Write-Host "============================================================"

foreach ($test in $tests) {

    Write-Host ""
    Write-Host "Ejecutando: $test"
    Write-Host ""

    python $test

    if ($LASTEXITCODE -ne 0) {

        Write-Host ""
        Write-Host "[ERROR] Test fallido: $test"

        exit $LASTEXITCODE
    }
}

Write-Host ""
Write-Host "============================================================"
Write-Host " TODOS LOS TESTS PASARON CORRECTAMENTE"
Write-Host "============================================================"
