# -*- mode: python ; coding: utf-8 -*-
import sys
import os
project_dir = os.path.abspath(os.path.dirname('.'))
sys.path.append(os.path.abspath(os.path.dirname('.')))

import glob
import pkgutil
import src.actions

template_files = [(file, 'src/templates') for file in glob.glob('src/templates/*.*')]
js_files = [(file, 'src/js') for file in glob.glob('src/js/*.js')]

hiddenimports = [
    f"src.actions.{module_name}"
    for _, module_name, _ in pkgutil.iter_modules(src.actions.__path__)
]

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('README.md', '.')] + template_files + js_files + [('src/axe-core/axe.min.js', 'src/axe-core')],
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
    [],
    exclude_binaries=True,
    name='wcag_checker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)

import zip_executable
zip_executable.main()

