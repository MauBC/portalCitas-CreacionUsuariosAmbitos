# Verificaciones en GitHub

`.github/workflows/validate.yml` se ejecuta en Pull Requests hacia `main`, pushes
a `main` o `codex/**`, y bajo demanda desde Actions. Usa Windows y Python 3.12.

El job `Local tests and packaged GUI` instala dependencias en el runner,
comprueba su compatibilidad, compila Python, revisa espacios y ejecuta
`tests/run_tests.ps1 -Suite Local` con Windows PowerShell. Despues construye
el ejecutable y ejecuta su self-check offline.

No necesita secretos ni `.env`. Las pruebas de integracion (`test_01` a
`test_04`) permanecen manuales porque requieren SharePoint, PostgreSQL y datos
operativos. El workflow no las ejecuta ni modifica fuentes remotas.

Las acciones se fijan a commits de sus versiones v6 y el token solo recibe
`contents: read`. El checkout no conserva credenciales en Git. Para actualizar
una accion, revisar su release y reemplazar deliberadamente el commit fijado.

La configuracion usa las interfaces oficiales de
[checkout](https://github.com/actions/checkout) y
[setup-python](https://github.com/actions/setup-python).

## Activacion

El workflow se incorpora al publicar esta rama. Sus ejecuciones reales se
consultan en la pestana Actions y en los checks del Pull Request. Una prueba
local equivalente no constituye una ejecucion verificada de GitHub Actions.

Para exigir el check antes de fusionar, un administrador puede seleccionarlo
en las reglas de proteccion de `main` despues de su primera ejecucion. Agregar
el archivo YAML no cambia por si solo esas reglas del repositorio.
