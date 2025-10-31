# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['ipchanger_v2.py'],
    pathex=[],
    binaries=[],
    datas=[('i18n', 'i18n'), ('*.json', '.')],
    hiddenimports=['ipchanger_enhanced', 'advanced_networking'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='NetworkIPChanger_CLI_v2.0.0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
