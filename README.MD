# Automatizacion de Usuarios y Ambitos

Aplicacion de escritorio en Python para preparar y validar cargas del Portal de Citas para Peru y El Salvador. Incluye GUI PySide6 y un backend organizado por fase y pais.

## Inicio

Desde la raiz del proyecto, con las dependencias de `requirements.txt` instaladas y `.env` configurado:

```powershell
conda activate excel_gui
python run_gui.py
```

La GUI integra Usuarios, Resultado del Portal y Ambitos, con seleccion de pais y navegacion guiada. `run.py` conserva la interfaz legacy en CustomTkinter.

Desde **Historial** puedes consultar nuevas ejecuciones de la GUI, abrir sus
archivos y recuperar entradas. Para trabajos anteriores al historial, usa
**Recuperar carpeta anterior** y confirma el pais. Se requiere un nuevo preview;
el historial no acredita el estado actual de SharePoint. Revisa siempre el
enlace compartido, que se toma de la configuracion actual.

**Conexion** comprueba PostgreSQL y metadatos de SharePoint cuando pulsas el
boton. Activa la VPN primero. No modifica datos ni comprueba permisos de
escritura sobre cada archivo.

Consultar [arquitectura y mantenimiento](docs/arquitectura.md) para el mapa de componentes, contratos y convenciones de desarrollo.

Para instalar las dependencias de ejecucion:

```powershell
python -m pip install -r requirements.txt
```

El ejecutable PySide6 se genera con `tools/build_gui.ps1`. Ver la
[guia de distribucion Windows](docs/distribucion.md) para crear un entorno de
compilacion, verificar el EXE y configurar el `.env` externo.

La [guia de integracion continua](docs/integracion-continua.md) describe las
pruebas y la compilacion automatica en GitHub, y como activar su verificacion
en los Pull Requests.

## Arquitectura por pais

| Pais | Fuente principal | Estado de creacion | Base de datos |
| --- | --- | --- | --- |
| PER | Excel de proveedores en SharePoint/OneDrive | columna `creado` | `DB_PER_NAME` |
| SLV | Lista SharePoint | columna `CREADO` | `DB_SLV_NAME` |

`DB_NAME` se conserva como fallback de configuracion.

## Fase 1 - Usuarios

La Fase 1 limpia, valida y genera:

```text
reporte_VALIDOS_*.xlsx / reporte_excel_VALIDOS_*.xlsx
reporte_ERRORES_*.xlsx / reporte_excel_ERRORES_*.xlsx
plantilla_usuarios_*.xlsx
usuarios_enviados.xlsx
```

### Peru

La fuente oficial es el Excel compartido con hoja `Proveedores`.

```powershell
python -m app.provider_excel_pipeline `
    --country PER `
    --source sharepoint `
    --url "https://..."
```

Para pruebas puede usarse una copia local:

```powershell
python -m app.provider_excel_pipeline `
    --country PER `
    --source local `
    --file "C:\ruta\usuarios.xlsx"
```

### El Salvador

SLV usa la lista SharePoint definida en `.env`.

El pipeline principal de usuarios se encuentra en:

```text
app/main_pipeline.py
```

## Fase 2 - Resultado del Portal

Estados de creacion:

```text
0 o vacio = pendiente
1          = creado / cuenta disponible
2          = error / no creado
```

`USUARIO YA EXISTE` se considera cuenta disponible.

### Peru

El flujo recomendado desde la GUI es **Preview -> Generar copia local actualizada -> Reemplazo manual en SharePoint -> Verificar reemplazo**. La generacion de la copia y la verificacion no escriben en SharePoint. Fase 3 requiere los estados publicados en el archivo remoto.

Preview:

```powershell
python -m app.provider_phase2_pipeline `
    --run-folder "C:\ruta\salidas\excel_proveedores_..." `
    --portal-result "C:\ruta\Resultado de usuarios.xlsx" `
    --url "https://..."
```

Aplicacion remota directa (opcion avanzada; un Excel abierto puede devolver HTTP 423):

```powershell
python -m app.provider_phase2_apply_pipeline `
    --run-folder "C:\ruta\salidas\excel_proveedores_..." `
    --portal-result "C:\ruta\Resultado de usuarios.xlsx" `
    --url "https://..."
```

El apply genera backup, objetivo, copia verificada y reporte antes de considerar cerrada la actualizacion.

### El Salvador

SLV procesa el resultado mediante:

```python
from app.phase2_pipeline import run_phase2
```

Se recomienda ejecutar primero con `dry_run=True`.

## Fase 3 - Ambitos

Fase 3 procesa solamente relaciones con estado de creacion `1`.

Funciones principales:

```python
from app.phase3_pipeline import run_phase3_preview, run_phase3_final
```

### Peru - DOLLARCITY

Configuracion validada:

```text
Cliente            : DOLLARCITY
RUC                 : 20606109343
Relacion Nueva      : grupo 1
Tipo de negocio     : grupo 4 / Retail
Sede Nueva          : grupo 1
Sede                : RSA
Tipo sede           : Centros de Distribucion
```

PER debe ejecutarse con `country_code="PER"` y la URL del Excel compartido.

### El Salvador

Configuracion validada:

```text
CALLEJA S.A : Relacion Nueva 1
DOCTOR SV   : Relacion Nueva 2

Sedes:
1 = RANSA APOPA
2 = RANSA SANTA ELENA
```

## Reglas principales

### Peru

- RUC proveedor: 11 digitos.
- DNI obligatorio.
- Un DNI con formato inusual genera advertencia.
- Servicio: `PORTAL ACCESO`.
- DOLLARCITY y sus aliases conocidos se homologan al cliente canonico.

### El Salvador

- NIT proveedor: 14 digitos.
- DUI obligatorio.
- Un DUI con formato inusual genera advertencia.
- Servicio: `PORTAL ACCESO CAM`.
- Clientes configurados: CALLEJA S.A y DOCTOR SV.

### Correos repetidos

Un correo representa una sola cuenta.

- La primera fila valida define la identidad de la cuenta.
- Las filas validas posteriores se conservan como relaciones adicionales.
- Una fila invalida no bloquea otra fila valida del mismo correo.

## Plantillas oficiales

```text
app/templates/subida_usuarios.xlsx
app/templates/subida_ambitos.xlsx
```

No deben reemplazarse manualmente.

## Configuracion

Crear `.env` a partir de `.env.example`.

Variables:

```text
MS_TENANT_ID
MS_CLIENT_ID
MS_CLIENT_SECRET
MS_GRAPH_SCOPE

SHAREPOINT_HOSTNAME
SHAREPOINT_SITE_PATH
SHAREPOINT_LIST_NAME

DB_HOST
DB_PORT
DB_NAME
DB_PER_NAME
DB_SLV_NAME
DB_USER
DB_PASSWORD
DB_SCHEMA
DB_SSLMODE

FILTER_ONLY_PENDING_SHAREPOINT
VALIDATE_EMAIL_EXISTS_IN_DB
```

`.env`, copias locales de `.env` y `usuarios.xlsx` no deben subirse a Git.

## Pruebas

El runner descubre todos los scripts `test_*.py` y permite separar pruebas locales de integracion. Por defecto ejecuta toda la suite y se detiene ante el primer fallo.

```powershell
.\tests\run_tests.ps1 -List
.\tests\run_tests.ps1 -Suite Local
.\tests\run_tests.ps1 -Suite Integration
.\tests\run_tests.ps1 -Suite All
```

Las pruebas de integracion (`test_01` a `test_04`) requieren `.env`, acceso a Graph/SharePoint y PostgreSQL; generan archivos de ejecucion en `salidas/`. Las locales no requieren conexiones reales.

Para elegir el interprete explicitamente:

```powershell
.\tests\run_tests.ps1 -Suite Local -Python "$env:USERPROFILE\miniconda3\envs\excel_gui\python.exe"
```

Tambien se pueden ejecutar individualmente:

```powershell
python .\tests\test_00_limpieza_paises.py
python .\tests\test_01_sistema.py
python .\tests\test_02_usuarios.py
python .\tests\test_03_ambitos.py
python .\tests\test_04_ambitos_final.py
python .\tests\test_05_excel_proveedores.py
python .\tests\test_06_validacion_compartida.py
python .\tests\test_07_estado_creado_excel.py
python .\tests\test_08_reporte_errores.py
python .\tests\test_10_prioridad_correo_repetido.py
python .\tests\test_11_cliente_per.py
python .\tests\test_12_apellidos_portal.py
python .\tests\test_13_reporte_negocio.py
python .\tests\test_14_fase2_per.py
python .\tests\test_15_fase2_per_apply.py
python .\tests\test_16_ambitos_per.py
```

Compilacion:

```powershell
python -m compileall -q .\app .\tests
```

## Seguridad operativa

- Revisar preview antes de cualquier escritura real.
- No sobrescribir manualmente las plantillas oficiales.
- No subir secretos o data operativa al repositorio.
- Los archivos generados se guardan en `salidas/`.
- `run.py` corresponde a la GUI antigua y no es el entrypoint oficial del backend actual.

## Tipo Usuario en Entidades

En la plantilla de Ambitos, la columna `Tipo Usuario` de la hoja `Entidades` se completa segun el tipo de entidad:

- Proveedor -> PROVEEDOR
- Cliente -> CLIENTE

Ejemplo para Peru:

- BUSINESS MFP SOLUTION PERU SAC -> PROVEEDOR
- DOLLARCITY -> CLIENTE

La misma regla aplica a los clientes y proveedores configurados para otros paises.

## Comportamiento observado del Portal al crear nuevas entidades

Durante una carga real se observo que, cuando un proveedor aun no existe en el Portal, la misma plantilla puede incluir tanto la creacion de la entidad como su nueva relacion.

En la primera carga, el Portal puede crear correctamente la nueva entidad y al mismo tiempo devolver en `RelacionNueva` un mensaje similar a:

`El documento XXXXX (nueva relacion) no existe`

Esto ocurre porque la nueva entidad todavia no estaba disponible cuando el Portal valido la relacion.

Una segunda carga del mismo archivo, una vez creadas las entidades, permite completar esas relaciones.

Por este motivo, este mensaje no implica necesariamente un error en la plantilla generada por el backend.
