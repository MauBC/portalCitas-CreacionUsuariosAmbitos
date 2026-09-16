from datetime import datetime
from pathlib import Path
import sys
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_ROOT = PROJECT_ROOT / "app" / "templates"
CONFIG_ROOT = PROJECT_ROOT / "app" / "config"


def get_runtime_root() -> Path:
    """External configuration and outputs live beside the executable in a build."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return PROJECT_ROOT


OUTPUT_ROOT = get_runtime_root() / "salidas"


def create_run_folder(
    prefix: str,
    output_root: str | Path | None = None,
) -> Path:
    base = Path(output_root) if output_root else OUTPUT_ROOT
    base.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    folder = base / f"{prefix}_{timestamp}"
    try:
        folder.mkdir(parents=False, exist_ok=False)
    except FileExistsError:
        # Windows clock resolution can yield the same timestamp for adjacent runs.
        folder = base / f"{prefix}_{timestamp}_{uuid4().hex}"
        folder.mkdir(parents=False, exist_ok=False)

    return folder
