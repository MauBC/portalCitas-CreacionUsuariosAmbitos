# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

root = Path(SPECPATH)
a = Analysis(
    [str(root / "run_gui.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "app/templates/subida_usuarios.xlsx"), "app/templates"),
        (str(root / "app/templates/subida_ambitos.xlsx"), "app/templates"),
        (str(root / "app/config/ambitos_config.json"), "app/config"),
        (str(root / "Ransalogo.ico"), "."),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=["PyQt5", "PyQt6", "PySide2", "customtkinter", "tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="AutomatizacionUsuarios",
    icon=str(root / "Ransalogo.ico"),
    debug=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False,
    upx=False,
    name="AutomatizacionUsuarios",
)
