# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# Get the current directory
current_dir = Path(SPECPATH)

block_cipher = None

# Define data files to include
datas = [
    # Include language files
    (str(current_dir / 'i18n'), 'i18n'),
    # Include icon file
    (str(current_dir / 'ip.ico'), '.'),
]

# Define hidden imports (for PySide6)
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtWidgets', 
    'PySide6.QtGui',
]

a = Analysis(
    ['ipchanger.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NetworkIPChanger',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for windowed app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(current_dir / 'ip.ico'),  # Set the icon
    uac_admin=True,  # Request admin privileges automatically
)