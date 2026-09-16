# Arquitectura y mantenimiento

La aplicacion prepara cargas del Portal de Citas de Ransa para PER y SLV.
La carga de las plantillas al Portal es manual. El resultado devuelto por el
Portal se reconcilia antes de generar ambitos.

## Capas

| Capa | Ubicacion | Responsabilidad |
| --- | --- | --- |
| Entrada GUI | `run_gui.py` | Cargar entorno e iniciar PySide6. |
| Presentacion | `app/ui/pages`, `app/ui/dialogs`, `app/ui/styles.py` | Recoger entradas, mostrar resultados y validar campos. |
| Trabajo en segundo plano | `app/ui/workers` | Invocar pipelines y comunicar progreso, resultados y errores. |
| Orquestacion | `app/*pipeline.py` | Coordinar las fases, servicios y archivos de una ejecucion. |
| Negocio | `app/services` | Limpiar, validar, reconciliar y generar reportes y plantillas. |
| Integraciones | `app/clients`, `app/auth` | Acceder a Graph, SharePoint y PostgreSQL. |
| Configuracion | `app/config` | Definir rutas, entorno, reglas por pais, clientes y sedes. |
| Recursos oficiales | `app/templates` | Conservar los libros base exigidos por el Portal. |

Los workers mantienen las operaciones de red y procesamiento fuera del hilo
visual. Las reglas de negocio deben permanecer en servicios y pipelines.

Mientras una fase procesa, la pagina bloquea sus controles y emite
`busy_changed`. La ventana bloquea el cambio de pais y de fase, y rechaza el
cierre con un aviso hasta que finalice el hilo. El progreso sigue visible.
Los controles se recuperan despues del resultado o error y la limpieza del
hilo. La senal `QThread.finished` programa la eliminacion del worker; el
controlador espera la salida completa del hilo antes de eliminarlo.
`test_23_gui_operaciones.py` verifica estos casos con hilos Qt reales y
servicios simulados, sin usar la red.

`run.py` es la interfaz legacy y se conserva para ejecucion desde codigo.
`AutomatizacionUsuarios.spec` empaqueta `run_gui.py` y sus recursos oficiales.
La configuracion privada permanece externa; ver [distribucion](distribucion.md).

## Mapa de flujos

| Fase | PER | SLV |
| --- | --- | --- |
| 1: usuarios | `provider_excel_pipeline.py` | `main_pipeline.py` |
| 2: resultado | `provider_phase2_pipeline.py`, `provider_phase2_apply_pipeline.py` | `phase2_pipeline.py` |
| 3: ambitos | `phase3_pipeline.py` | `phase3_pipeline.py` |

PER lee un Excel compartido (o local en Fase 1). SLV lee una lista SharePoint.
Cada pais usa su configuracion de PostgreSQL. Los resultados se guardan en
`salidas/`; `usuarios_enviados.xlsx` vincula la Fase 1 con la Fase 2.

Para PER, el flujo recomendado de Fase 2 es preview, copia local actualizada,
reemplazo manual del archivo compartido y verificacion del reemplazo.
El Apply remoto permanece como opcion avanzada. Generar la copia local no
consolida el estado publicado ni habilita por si solo el paso a Ambitos.

## Contratos que deben preservarse

- Un email representa una cuenta. El primer registro valido define su identidad;
  las relaciones adicionales validas permanecen disponibles para las otras fases.
- Fase 1 no escribe estados de creacion en SharePoint.
- Fase 2 propaga el resultado de la cuenta a sus relaciones validas. No debe
  degradar estados remotos cerrados ni dar por creado a un usuario solo por enviarlo.
- Fase 3 consulta el estado publicado y procesa solo relaciones con `creado=1`.
  No sustituye el remoto por una copia local pendiente de publicacion.
- Las plantillas conservan su estructura oficial. La actualizacion del Excel PER
  preserva formulas, caches y los componentes XLSX no afectados.
- Los clientes desconocidos siguen el tratamiento de validacion o revision
  correspondiente; no se asignan silenciosamente a un cliente conocido.
- Las entidades proveedor usan `PROVEEDOR`; las entidades cliente usan `CLIENTE`.

## Validacion de cambios

El runner sigue usando scripts Python ejecutables; no requiere pytest.
Desde la raiz, con el entorno `excel_gui` activo:

```powershell
.\tests\run_tests.ps1 -Suite Local
.\tests\run_tests.ps1 -Suite Integration
.\tests\run_tests.ps1 -Suite All
python -m compileall -q app tests run_gui.py
git diff --check
```

`Local` incluye scripts con datos locales, temporales o dobles de
prueba. `Integration` incluye `test_01` a `test_04`: necesita `.env`, acceso a
Graph/SharePoint y PostgreSQL y datos operativos compatibles. Genera archivos
en `salidas/`. Su orden es relevante: Fase 1 prepara los archivos de Ambitos.
Un fallo de conectividad no demuestra una regresion del codigo.

El runner descubre `test_*.py`, los ordena por nombre y se detiene en el primer
fallo, mostrando las pruebas ejecutadas y devolviendo un codigo distinto de cero.
Por defecto ejecuta `All`. `-List` permite revisar la seleccion sin ejecutar nada.
`-Python` admite la ruta de un interprete para no depender del Python del PATH.
El runner fija temporalmente el directorio de trabajo a la raiz del proyecto.

Al agregar un test que use servicios reales, incluir su nombre en
`$integrationTests` del runner; los demas tests se clasifican como locales.
No hay un `test_09` en la suite actual: el descubrimiento no requiere numeracion
consecutiva. Las pruebas individuales tambien pueden ejecutarse directamente.

## Configuracion, rutas y diagnosticos

`GraphClient` reintenta HTTP 429, 500, 502, 503 y 504, respetando
`Retry-After` numerico o usando una espera exponencial cuando no esta presente.
Los errores HTTP permanentes, certificados invalidos y JSON invalido no se
repiten. Los errores de transporte se reintentan solo para lecturas GET/HEAD:
un PATCH sin respuesta puede haberse aplicado y requiere comprobar el estado
antes de repetirlo. El error final conserva su causa para diagnostico.
`max_retries` mantiene su significado existente de numero total de intentos.
`test_26_graph_reintentos.py` valida la politica sin solicitudes reales.
Referencia: [limites y reintentos de Graph](https://learn.microsoft.com/en-us/graph/throttling).

`PostgresClient.fetch_all` cierra la conexion despues de cada consulta, tanto
si termina correctamente como si falla la consulta o la transaccion. Conserva
el commit/rollback del contexto de psycopg2 y propaga el error original.
Quien use directamente `get_connection()` debe cerrar la conexion recibida.

`DB_CONNECT_TIMEOUT` limita el intento de conexion en segundos: por defecto
15, con un minimo de 2. Es opcional en los archivos `.env` existentes. No
limita la duracion de las consultas ni sustituye el acceso por VPN; libpq lo
aplica por destino de conexion, no como limite global del flujo. Ver
[conexion PostgreSQL](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNECT-CONNECT-TIMEOUT)
y [contextos psycopg2](https://www.psycopg.org/docs/usage.html#with-statement).
`test_24_postgres_conexiones.py` verifica errores, liberacion de recursos y
configuracion del timeout sin conectarse a servicios reales.

`app/config/paths.py` centraliza las rutas de recursos y salidas. Los recursos
se resuelven desde el codigo; el `.env` y las salidas se ubican en la raiz del
proyecto durante desarrollo y junto al ejecutable cuando esta empaquetado.
Las carpetas de ejecucion conservan su prefijo y fecha; si dos ejecuciones
comparten timestamp, la segunda recibe un sufijo unico.

`load_env()` exige un `.env` para los entrypoints existentes. Los servicios que
importan `settings` usan `load_env(required=False)` para poder ejecutarse con
variables del proceso o datos de prueba sin un archivo local. Las variables
ya presentes en el proceso tienen prioridad. No se busca un `.env` en la
carpeta actual ni en directorios ajenos al proyecto.

Los errores de las tres paginas GUI se guardan en
`salidas/error_gui_<timestamp>/error.log`, con fecha, fase, pais, modo y traza.
El detalle del dialogo incluye la ruta. El servicio elimina los valores
configurados de `MS_CLIENT_SECRET` y `DB_PASSWORD`, ademas de campos comunes de
credenciales. Los reportes siguen siendo diagnosticos locales y pueden contener
datos operativos; no se versionan. Si no se puede escribir el log, el dialogo
conserva el diagnostico para que el error de disco no oculte el fallo original.

`test_17_configuracion_logs.py` verifica estos contratos y
`test_18_gui_errores.py` comprueba las tres paginas con Qt offscreen, sin abrir
ventanas ni conectarse a servicios reales. La ruta de ejecutable se prueba
mediante simulacion y el build realiza ademas un self-check del EXE real.

## Componentes compartidos de interfaz

`app/ui/file_actions.py` abre archivos y carpetas generados. Comprueba que el
destino exista y muestra un aviso si el sistema no puede abrirlo. Las tres
paginas delegan esta accion al mismo componente.

`app/ui/widgets/field_feedback.py` aplica los estados visuales `invalid` y
`valid`, y muestra o limpia los mensajes junto al campo. Cada pagina conserva
sus reglas de validacion y decide cuando aplicar esos estados. La seleccion
entre Excel local y SharePoint de Fase 1 mantiene su comportamiento especifico.

`test_19_gui_componentes.py` verifica la apertura sin lanzar aplicaciones reales,
los errores por archivo ausente o sin aplicacion asociada y las transiciones
de los campos entre error, valido y neutro en las tres paginas.

## Vista y contratos de presentacion

Al iniciar otro preview, Fase 2 y Ambitos invalidan el resultado previo antes
de ejecutar el worker. Un fallo no rehabilita las acciones del intento anterior.
Cambiar las entradas elimina las referencias visuales a copias, resultados
finales y revisiones anteriores, pero conserva los archivos en disco.

La firma del preview incluye tamano, fecha de modificacion e identidad de los
archivos locales (resultado del Portal y manifiesto en Fase 2; reporte VALIDOS
en Ambitos). Si cambian durante el preview, el resultado se descarta. Las
acciones posteriores comparan nuevamente la firma. Esta comprobacion no es
un hash del contenido ni verifica cambios remotos. La revision manual de
clientes puede editarse despues del preview, como requiere el flujo de Ambitos.
`test_25_preview_vigencia.py` cubre resultados obsoletos y refrescos fallidos.

`Phase2Page` conserva el estado del flujo, los workers y las verificaciones
necesarias para habilitar acciones. Su base visual `Phase2View` construye las
tarjetas de archivos, acciones y resultados sin cargar ajustes ni ejecutar
operaciones. La pagina conecta explicitamente los eventos despues de cargar
los valores guardados. La vista se puede instanciar sin controlador.

`app/ui/result_models.py` adapta los diccionarios existentes a modelos de
presentacion inmutables: `Phase1Summary`, `Metric`, `ResultFiles` y
`Phase2Presentation`. Tambien normaliza las metricas de Ambitos. No modifica
los diccionarios recibidos ni decide si se permite una escritura remota.
Las cuentas unicas y las relaciones permanecen como cantidades independientes.

`test_20_fase2_gui_flujo.py` protege la secuencia preview, copia local,
verificacion y habilitacion de Ambitos. `test_21_resultados_gui.py` verifica
los adaptadores de PER/SLV y los conteos por cuenta y relacion.

## Convenciones para los siguientes checkpoints

- Usar `.editorconfig`: UTF-8, espacios y salto final. No reformatear todo el
  repositorio junto con un cambio funcional.
- Mantener funciones pequenas por responsabilidad, nombres explicitos y tipos
  en los contratos nuevos. Reutilizar servicios antes de duplicar logica en GUI.
- Verificar pruebas relacionadas en cambios acotados y la suite completa en
  cambios transversales. Inspeccionar siempre el diff antes del commit.
- No versionar `.env`, datos operativos, `salidas/` ni los TXT temporales de
  contexto. Agregar archivos al staging explicitamente.
