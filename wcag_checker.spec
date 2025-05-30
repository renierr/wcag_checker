# -*- mode: python ; coding: utf-8 -*-
import sys
import os
project_dir = os.path.abspath(os.path.dirname('.'))
sys.path.append(os.path.abspath(os.path.dirname('.')))

import glob
import pkgutil
import src.actions
from PyInstaller.utils.hooks import collect_data_files

axe_data_files = collect_data_files('selenium_axe_python')
template_files = [(file, 'src/templates') for file in glob.glob('src/templates/*.*')]
hiddenimports = [
    f"src.actions.{module_name}"
    for _, module_name, _ in pkgutil.iter_modules(src.actions.__path__)
]

a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('README.md', '.')] + template_files + axe_data_files + [('src/axe-core/axe.min.js', 'src/axe-core')],
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
    name='wcag_checker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
