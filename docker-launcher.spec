# PyInstaller spec for docker-launcher
# Produces a folder distribution with exe + supporting files.
# Usage: pyinstaller docker-launcher.spec

block_cipher = None

a = Analysis(
    ["boot.py"],
    pathex=["src"],
    binaries=[],
    datas=[
        ("src/docker_launcher/static", "docker_launcher/static"),
        ("images", "images"),
    ],
    hiddenimports=[
        "docker_launcher",
        "docker_launcher.main",
        "docker_launcher.docker_service",
        "docker_launcher.database",
        "docker_launcher._auth_defaults",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="docker-launcher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="docker-launcher",
)
