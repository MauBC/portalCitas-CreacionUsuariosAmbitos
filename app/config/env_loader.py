from pathlib import Path

from dotenv import load_dotenv

from app.config.paths import get_runtime_root


def load_env(*, required: bool = True) -> Path:
    """Load the project's explicit .env without overriding process variables.

    GUI/legacy entrypoints require the file; pure backend services may use only
    environment variables. The current working directory never selects a .env.
    """
    env_path = get_runtime_root() / ".env"
    if not env_path.is_file():
        if required:
            raise FileNotFoundError(f"No se encontro el archivo .env en: {env_path}")
        return env_path
    load_dotenv(env_path, override=False)
    return env_path
