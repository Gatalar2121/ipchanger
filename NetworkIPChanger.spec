# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui', 'PySide6.QtWidgets.QApplication', 'PySide6.QtWidgets.QWidget', 'PySide6.QtWidgets.QMainWindow', 'PySide6.QtWidgets.QVBoxLayout', 'PySide6.QtWidgets.QHBoxLayout', 'PySide6.QtWidgets.QLabel', 'PySide6.QtWidgets.QPushButton', 'PySide6.QtWidgets.QComboBox', 'PySide6.QtWidgets.QLineEdit', 'PySide6.QtWidgets.QTextEdit', 'PySide6.QtWidgets.QMessageBox', 'PySide6.QtWidgets.QFileDialog', 'PySide6.QtWidgets.QGroupBox', 'PySide6.QtWidgets.QRadioButton', 'PySide6.QtWidgets.QButtonGroup', 'PySide6.QtWidgets.QFormLayout', 'PySide6.QtWidgets.QListWidget', 'PySide6.QtWidgets.QListWidgetItem', 'PySide6.QtWidgets.QInputDialog', 'PySide6.QtWidgets.QSizePolicy', 'PySide6.QtWidgets.QSpacerItem', 'shiboken6']
hiddenimports += collect_submodules('PySide6')


a = Analysis(
    ['ipchanger.py'],
    pathex=[],
    binaries=[],
    datas=[('i18n', 'i18n'), ('ip.ico', '.')],
    hiddenimports=hiddenimports,
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
    name='NetworkIPChanger',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon=['ip.ico'],
)
