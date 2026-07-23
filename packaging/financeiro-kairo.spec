from pathlib import Path

project_root = Path(SPECPATH).parent
entrypoint = project_root / "src/financeiro_kairo/presentation/main.py"
source_root = project_root / "src"

analysis = Analysis(
    [str(entrypoint)],
    pathex=[str(source_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "financeiro_kairo.domain.models",
        "financeiro_kairo.domain.planning_models",
        "financeiro_kairo.domain.recurring_expenses",
        "pandas",
        "openpyxl",
        "reportlab",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="financeiro-kairo",
    console=False,
    strip=False,
    upx=False,
)
