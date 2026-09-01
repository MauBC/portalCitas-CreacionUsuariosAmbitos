import os
import json
import time
import traceback
from datetime import datetime
from google import genai


class GeminiClientParserService:
    def __init__(
        self,
        service_account_file: str = "clave_ambitos_carga.json",
        location: str = "global",
        model_name: str = "gemini-3-flash-preview",
        max_retries: int = 3,
    ):
        self.service_account_file = service_account_file
        self.location = location
        self.model_name = model_name
        self.max_retries = max_retries

        with open(self.service_account_file, "r", encoding="utf-8") as f:
            creds = json.load(f)

        self.project_id = creds["project_id"]
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.service_account_file

        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location,
        )

    def parse_providers_clients(
        self,
        providers: list[dict],
        batch_size: int = 25,
        output_dir: str | None = None,
    ) -> dict:
        start_time = time.time()

        all_results = []
        all_errors = []
        logs = []

        total_batches = (len(providers) + batch_size - 1) // batch_size

        for batch_index, start in enumerate(range(0, len(providers), batch_size), start=1):
            batch = providers[start:start + batch_size]

            logs.append(
                f"[{datetime.now()}] Procesando lote {batch_index}/{total_batches} con {len(batch)} proveedores."
            )
            print(f"Procesando lote {batch_index}/{total_batches} con {len(batch)} items...")

            batch_response = self._parse_batch_with_retry(
                batch=batch,
                batch_index=batch_index,
                total_batches=total_batches,
            )   
            print(f"Procesando lote {batch_index}/{total_batches} con {len(batch)} items...")

            all_results.extend(batch_response["results"])
            all_errors.extend(batch_response["errors"])
            logs.extend(batch_response["logs"])

        elapsed_seconds = round(time.time() - start_time, 2)

        summary = {
            "total_proveedores": len(providers),
            "batch_size": batch_size,
            "total_lotes": total_batches,
            "resultados_ok": len(all_results),
            "errores": len(all_errors),
            "tiempo_segundos": elapsed_seconds,
            "modelo": self.model_name,
        }

        final_data = {
            "summary": summary,
            "resultados": all_results,
            "errores": all_errors,
        }

        if output_dir:
            self._save_outputs(output_dir, final_data, logs)

        return final_data

    def _parse_batch_with_retry(self, batch: list[dict], batch_index: int, total_batches: int) -> dict:
        logs = []
        errors = []

        for attempt in range(1, self.max_retries + 1):
            try:
                logs.append(
                    f"[{datetime.now()}] Lote {batch_index}/{total_batches} intento {attempt}."
                )

                results = self._parse_batch(batch)

                logs.append(
                    f"[{datetime.now()}] Lote {batch_index}/{total_batches} procesado correctamente."
                )

                return {
                    "results": results,
                    "errors": [],
                    "logs": logs,
                }

            except Exception as e:
                error_detail = {
                    "batch_index": batch_index,
                    "attempt": attempt,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "traceback": traceback.format_exc(),
                    "items": batch,
                }

                logs.append(
                    f"[{datetime.now()}] Error en lote {batch_index}/{total_batches}, intento {attempt}: {type(e).__name__} - {str(e)}"
                )

                if attempt < self.max_retries:
                    wait_seconds = min(2 ** attempt, 20)
                    logs.append(
                        f"[{datetime.now()}] Reintentando lote {batch_index} en {wait_seconds} segundos."
                    )
                    time.sleep(wait_seconds)
                else:
                    errors.append(error_detail)

        fallback_results = self._build_fallback_results(batch)

        return {
            "results": fallback_results,
            "errors": errors,
            "logs": logs,
        }

    def _parse_batch(self, batch: list[dict]) -> list[dict]:
        payload = [
            {
                "item_id": item.get("item_id"),
                "input_clientes": item.get("input_clientes"),
            }
            for item in batch
        ]

        prompt = self._build_prompt(payload)


        print("Enviando request a Gemini...")

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "temperature": 0.0,
                "response_mime_type": "application/json",
            },
        )
        print("Respuesta recibida de Gemini.")
        if not response or not response.text:
            raise ValueError("Gemini devolvio una respuesta vacia.")

        data = json.loads(response.text)

        if not isinstance(data, dict):
            raise ValueError("Gemini no devolvio un objeto JSON.")

        if "resultados" not in data:
            raise ValueError("Gemini no devolvio la clave 'resultados'.")

        if not isinstance(data["resultados"], list):
            raise ValueError("La clave 'resultados' no es una lista.")

        return self._validate_results(data["resultados"])

    def _validate_results(self, results: list[dict]) -> list[dict]:
        validated = []

        for item in results:
            input_clientes = item.get("input_clientes")
            clientes_detectados = item.get("clientes_detectados", [])

            if not isinstance(clientes_detectados, list):
                clientes_detectados = []

            cleaned_clients = []

            for client in clientes_detectados:
                cleaned_clients.append({
                    "cliente_input": client.get("cliente_input"),
                    "cliente_canonico_sugerido": client.get("cliente_canonico_sugerido"),
                    "grupo_economico": client.get("grupo_economico"),
                    "confianza": client.get("confianza", "baja"),
                    "requiere_revision_manual": bool(client.get("requiere_revision_manual", False)),
                })

            validated.append({
                "item_id": item.get("item_id"),
                "input_clientes": input_clientes,
                "clientes_detectados": cleaned_clients,
                "observacion": item.get("observacion", ""),
            })

        return validated

    def _build_fallback_results(self, batch: list[dict]) -> list[dict]:
        fallback = []

        for item in batch:
            fallback.append({
                "item_id": item.get("item_id"),
                "input_clientes": item.get("input_clientes"),
                "clientes_detectados": [],
                "observacion": "ERROR_GEMINI: no se pudo procesar este proveedor despues de los reintentos.",
            })
        return fallback

    def _save_outputs(self, output_dir: str, data: dict, logs: list[str]) -> None:
        os.makedirs(output_dir, exist_ok=True)

        results_path = os.path.join(output_dir, "gemini_clientes_normalizados.json")
        errors_path = os.path.join(output_dir, "gemini_clientes_errores.json")
        log_path = os.path.join(output_dir, "gemini_clientes_log.txt")

        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "summary": data["summary"],
                    "resultados": data["resultados"],
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        with open(errors_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "summary": data["summary"],
                    "errores": data["errores"],
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(logs))

    def _build_prompt(self, items: list[dict]) -> str:
        items_json = json.dumps(items, ensure_ascii=False, indent=2)

        return f"""
Eres un asistente de normalizacion de datos empresariales en Peru.

Recibiras entradas con:
- item_id
- input_clientes

El campo input_clientes puede contener uno o varios clientes escritos de forma sucia.
Puede incluir marcas comerciales, razones sociales incompletas, sedes, errores ortograficos o varios clientes separados por comas, saltos de linea, guiones, slash o punto y coma.

IMPORTANTE:
Debes devolver EXACTAMENTE el mismo item_id para cada item.

Tareas:
1. Separar clientes mencionados en input_clientes.
2. Sugerir cliente_canonico_sugerido.
3. Si aplica, incluir grupo_economico, pero debe ser solo un valor.
4. No devuelvas grupos combinados como "NGR / INTERCORP".
5. Si existe un grupo operador mas especifico, usa ese y no el holding mayor.
6. Ejemplo: si el cliente pertenece a NGR y NGR pertenece a Intercorp, devuelve "NGR", no "INTERCORP" ni "NGR / INTERCORP".
7. Si no sabes, usa null y confianza baja.

- El cliente_canonico_sugerido debe ser la razon social, empresa operadora o cliente empresarial mas probable.
- grupo_economico debe contener solo un nombre.
- No uses slash, coma ni multiples grupos en grupo_economico.
- Prioriza el grupo operador o unidad de negocio sobre el holding corporativo general.

Devuelve exclusivamente JSON valido:

{{
  "resultados": [
    {{
      "item_id": "int",
      "input_clientes": "string",
      "clientes_detectados": [
        {{
          "cliente_input": "string",
          "cliente_canonico_sugerido": "string o null",
          "grupo_economico": "string o null",
          "confianza": "alta|media|baja",
          "requiere_revision_manual": true
        }}
      ]
    }}
  ]
}}

Datos:
{items_json}
"""