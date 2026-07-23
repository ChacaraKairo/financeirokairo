from PyInstaller.utils.hooks import collect_all

pyside_data, pyside_bins, pyside_hidden = collect_all("PySide6")

analysis = Analysis(
    ["src/financeiro_kairo/presentation/app.py"],
    pathex=["src"],
    binaries=pyside_bins,
    datas=pyside_data,
    hiddenimports=pyside_hidden + [
        "financeiro_kairo.domain.models",
        "financeiro_kairo.domain.planning_models",
        "pandas",
        "openpyxl",
        "reportlab",
    ],
    noarchive=False,
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
