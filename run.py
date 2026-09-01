from app.config.env_loader import load_env

load_env()

import os
import glob
import threading
import traceback
import pandas as pd
import customtkinter as ctk

from tkinter import messagebox, filedialog
from datetime import datetime

from app.main_pipeline import run_pipeline
from app.services.db_validation_service import DbValidationService
from app.services.ambitos_builder_service import AmbitosBuilderService
from app.services.ambitos_excel_service import AmbitosExcelService


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class AutomatizacionApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.iconbitmap("Ransalogo.ico")
        self.title("Automatización Usuarios y Ámbitos")
        self.geometry("760x420")
        self.resizable(False, False)

        self.current_run_folder = None

        self.build_ui()

    def build_ui(self):
        title_label = ctk.CTkLabel(
            self,
            text="Automatización de Usuarios y Ámbitos",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(30, 10))

        desc_label = ctk.CTkLabel(
            self,
            text=(
                "Este proceso permite generar la plantilla de creación de usuarios "
                "y luego generar la plantilla de ámbitos usando la carpeta de ejecución."
            ),
            wraplength=660,
            justify="center"
        )
        desc_label.pack(pady=(0, 25))

        self.process_button = ctk.CTkButton(
            self,
            text="Ejecutar automatización de usuarios",
            command=self.start_process,
            width=280,
            height=42,
            fg_color="#25a55a",        # verde moderno
            hover_color="#398056"
        )
        self.process_button.pack(pady=(5, 12))

        self.ambitos_button = ctk.CTkButton(
            self,
            text="Generar plantilla de ámbitos",
            command=self.start_ambitos_process,
            width=280,
            height=42,
            fg_color="#25a55a",        # verde moderno
            hover_color="#398056"
        )
        self.ambitos_button.pack(pady=(0, 15))

        self.status_label = ctk.CTkLabel(
            self,
            text="Listo para ejecutar.",
            font=ctk.CTkFont(size=13)
        )
        self.status_label.pack(pady=(12, 5))

    def start_process(self):
        self.process_button.configure(state="disabled")
        self.ambitos_button.configure(state="disabled")
        self.status_label.configure(text="Procesando datos desde SharePoint...")
        self.current_run_folder = None

        thread = threading.Thread(target=self.run_process, daemon=True)
        thread.start()

    def run_process(self):
        try:
            result = run_pipeline()
            self.current_run_folder = result.get("run_folder")
            self.after(0, lambda: self.on_finish(result))
        except Exception as e:
            error_detail = f"{type(e).__name__}: {str(e)}"
            full_trace = traceback.format_exc()
            self.after(0, lambda: self.on_error(error_detail, full_trace))

    def on_finish(self, result: dict):
        self.process_button.configure(state="normal")
        self.ambitos_button.configure(state="normal")

        if not result["ok"]:
            self.status_label.configure(text=result["message"])
            messagebox.showwarning("Aviso", result["message"])
            return

        self.status_label.configure(text="Proceso de usuarios completado correctamente.")

        template_msg = (
            result["path_template"]
            if result["path_template"]
            else "No se generó plantilla porque no hubo válidos."
        )

        sharepoint_msg = (
            f"Filas actualizadas en SharePoint: {result.get('sharepoint_updated', 0)}\n"
            f"Fallos al actualizar SharePoint: {len(result.get('sharepoint_failed', []))}"
        )

        messagebox.showinfo(
            "Proceso completado",
            (
                f"Total registros evaluados: {result['total']}\n"
                f"Válidos: {result['validos']}\n"
                f"Errores: {result['errores']}\n"
                f"Correos existentes en BD: {result.get('correos_existentes_bd', 0)}\n\n"
                f"{sharepoint_msg}\n\n"
                f"Carpeta generada:\n{result.get('run_folder', 'No disponible')}\n\n"
                f"Excel de válidos:\n{result['path_validos']}\n\n"
                f"Excel de errores:\n{result['path_errores']}\n\n"
                f"Plantilla usuarios:\n{template_msg}"
            )
        )

    def start_ambitos_process(self):
        folder_path = filedialog.askdirectory(
            title="Seleccionar carpeta de ejecución"
        )

        if not folder_path:
            return

        self.process_button.configure(state="disabled")
        self.ambitos_button.configure(state="disabled")
        self.status_label.configure(text="Generando plantilla de ámbitos...")

        thread = threading.Thread(
            target=self.run_ambitos_process,
            args=(folder_path,),
            daemon=True
        )
        thread.start()

    def run_ambitos_process(self, folder_path: str):
        try:
            result = self.generate_ambitos_from_folder(folder_path)
            self.after(0, lambda: self.on_ambitos_finish(result))
        except Exception as e:
            error_detail = f"{type(e).__name__}: {str(e)}"
            full_trace = traceback.format_exc()
            self.current_run_folder = folder_path
            self.after(0, lambda: self.on_error(error_detail, full_trace))

    def generate_ambitos_from_folder(self, folder_path: str) -> dict:
        validos_path = self.find_validos_excel(folder_path)

        df_validos = pd.read_excel(validos_path, sheet_name="VALIDOS")

        db = DbValidationService()
        builder = AmbitosBuilderService()
        excel = AmbitosExcelService(output_dir=folder_path)

        clients = db.get_distinct_clients()
        data = builder.build(df_validos, clients)

        ambitos_path = excel.export_template_ambitos(data=data)

        log_content = (
            f"Fecha: {datetime.now()}\n"
            f"Archivo validos usado: {validos_path}\n"
            f"Clientes obtenidos BD: {len(clients)}\n"
            f"Entidades generadas: {len(data.get('entidades', []))}\n"
            f"RelacionNueva generadas: {len(data.get('relacion_nueva', []))}\n"
            f"Ambitos generados: {len(data.get('ambitos', []))}\n"
            f"Plantilla ambitos: {ambitos_path}\n"
        )

        log_path = os.path.join(folder_path, "ambitos_log.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(log_content)

        return {
            "ok": True,
            "folder_path": folder_path,
            "validos_path": validos_path,
            "ambitos_path": ambitos_path,
            "clientes_bd": len(clients),
            "entidades": len(data.get("entidades", [])),
            "relacion_nueva": len(data.get("relacion_nueva", [])),
            "ambitos": len(data.get("ambitos", [])),
            "log_path": log_path,
        }

    def find_validos_excel(self, folder_path: str) -> str:
        pattern = os.path.join(folder_path, "*VALIDOS*.xlsx")
        files = glob.glob(pattern)

        if not files:
            raise FileNotFoundError(
                f"No se encontro archivo VALIDOS en: {folder_path}"
            )

        files.sort(key=os.path.getmtime, reverse=True)
        return files[0]

    def on_ambitos_finish(self, result: dict):
        self.process_button.configure(state="normal")
        self.ambitos_button.configure(state="normal")
        self.status_label.configure(text="Plantilla de ámbitos generada correctamente.")

        messagebox.showinfo(
            "Plantilla de ámbitos generada",
            (
                f"Carpeta:\n{result['folder_path']}\n\n"
                f"Excel válidos usado:\n{result['validos_path']}\n\n"
                f"Clientes BD: {result['clientes_bd']}\n"
                f"Entidades: {result['entidades']}\n"
                f"RelacionNueva: {result['relacion_nueva']}\n"
                f"Ámbitos: {result['ambitos']}\n\n"
                f"Plantilla ámbitos:\n{result['ambitos_path']}\n\n"
                f"Log:\n{result['log_path']}"
            )
        )

    def on_error(self, error_detail: str, full_trace: str):
        self.process_button.configure(state="normal")

        if hasattr(self, "ambitos_button"):
            self.ambitos_button.configure(state="normal")

        self.status_label.configure(text="Ocurrió un error durante la automatización.")

        log_path = "error_log.txt"

        try:
            base_output_dir = os.path.abspath("salidas")
            os.makedirs(base_output_dir, exist_ok=True)

            if self.current_run_folder:
                run_folder = self.current_run_folder
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                run_folder = os.path.join(base_output_dir, f"ejecucion_error_{timestamp}")
                os.makedirs(run_folder, exist_ok=True)

            log_path = os.path.join(run_folder, "error_log.txt")

            with open(log_path, "w", encoding="utf-8") as f:
                f.write(full_trace)

        except Exception:
            pass

        messagebox.showerror(
            "Error",
            (
                f"No se pudo completar la automatización.\n\n"
                f"Detalle:\n{error_detail}\n\n"
                f"Log generado en:\n{log_path}"
            )
        )


if __name__ == "__main__":
    app = AutomatizacionApp()
    app.mainloop()