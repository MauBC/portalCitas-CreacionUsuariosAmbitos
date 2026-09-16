from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = PROJECT_ROOT / "salidas"


def create_run_folder(
    prefix: str,
    output_root: str | Path | None = None,
) -> Path:
    base = Path(output_root) if output_root else OUTPUT_ROOT
    base.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    folder = base / f"{prefix}_{timestamp}"
    folder.mkdir(parents=False, exist_ok=False)

    return folder
