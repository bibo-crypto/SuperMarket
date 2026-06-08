# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None
here = os.path.abspath(os.getcwd())

datas = []

a = Analysis(
    [os.path.join(here, "main.py")],
    pathex=[here],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="NoorMarket",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=os.path.join(here, "icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="NoorMarket",
)
