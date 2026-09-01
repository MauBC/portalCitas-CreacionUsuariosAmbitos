import os
import sys
from dotenv import load_dotenv


def load_env():
    """
    Carga el .env desde la misma carpeta del ejecutable o script.
    """

    if getattr(sys, 'frozen', False):
        # ejecutable (.exe)
        base_path = os.path.dirname(sys.executable)
    else:
        # modo desarrollo (python)
        base_path = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.abspath(os.path.join(base_path, "../../"))

    env_path = os.path.join(base_path, ".env")

    if not os.path.exists(env_path):
        raise FileNotFoundError(
            f"No se encontro el archivo .env en: {env_path}"
        )

    load_dotenv(env_path)