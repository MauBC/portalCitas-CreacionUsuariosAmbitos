# Distribucion Windows

La GUI se valida con Python 3.12. `requirements.txt` contiene las dependencias
directas de ejecucion con versiones fijadas, incluida PySide6. Conserva
CustomTkinter para ejecutar `run.py` desde codigo. `requirements-build.txt`
agrega PyInstaller y sus hooks; el ejecutable nuevo solo incluye PySide6.
Las dependencias transitivas las resuelve pip: estos archivos no son un lock
completo de todas las dependencias.

## Crear un entorno de compilacion

Desde la raiz del proyecto, con Python 3.12 disponible:

```powershell
python -m venv build\venv
.\build\venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\build\venv\Scripts\python.exe -m pip check
.\tools\build_gui.ps1 -Python .\build\venv\Scripts\python.exe
```

El build produce `dist/AutomatizacionUsuarios/AutomatizacionUsuarios.exe`.
Distribuir **toda la carpeta**, incluida `_internal`, que contiene librerias,
las dos plantillas oficiales, el JSON de ambitos y el icono. No mover solo el EXE.

El script ejecuta un self-check del EXE desde otra carpeta, con Qt offscreen.
Durante la compilacion y el self-check limita temporalmente PATH a Python y
Windows para no incluir DLLs incompatibles de otras herramientas instaladas.
Al terminar restaura el PATH de la sesion.
Verifica imports de pipelines, lectura de recursos, creacion de la ventana,
cambio de pais, navegacion y resize. El reporte queda en `build/` y un fallo
interrumpe el build. No ejecuta pipelines ni accede a Graph o PostgreSQL.

Tambien se puede comprobar desde codigo:

```powershell
python run_gui.py --self-check salidas\gui-self-check.json
```

## Configuracion de destino

El build no incluye `.env`, credenciales ni datos operativos. Copia solamente
`.env.example` como referencia. En el equipo de destino, crear un `.env` junto
al EXE usando esa referencia y configurar las credenciales por separado.
No renombrar `.env.example` en el repositorio de trabajo.

Si falta `.env`, la aplicacion muestra un dialogo con instrucciones. El usuario
necesita permisos de escritura en la carpeta de la aplicacion para `salidas/`.
Las conexiones reales siguen requiriendo acceso a SharePoint y PostgreSQL.

El self-check no certifica conectividad en otro equipo, permisos de Graph,
firma digital ni aceptacion por antivirus. La prueba operativa final se hace
con la configuracion del equipo de destino. El ejecutable generado no esta firmado.

## Referencias tecnicas

Las rutas de recursos siguen el contrato `__file__` de
[PyInstaller](https://pyinstaller.org/en/stable/runtime-information.html).
La lista de archivos incluidos se declara explicitamente en el
[spec de compilacion](https://pyinstaller.org/en/stable/spec-files.html),
sin copiar directorios completos con configuracion privada.
