# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_submodules

# 自动搜集所有用到的包（仅当你有动态导入时启用）
# hiddenimports = collect_submodules('your_optional_module')
hiddenimports = []

block_cipher = None

a = Analysis(
    ['QuickDaily.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets/icon.ico', 'assets'),
        ('assets/moon.png', 'assets'),
        ('assets/sun.png', 'assets'),
        ('assets/timer.png', 'assets'),
        ('assets/timer-off.png', 'assets'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'tkinter.test',
        'unittest',
        'email',
        'http',
        'xml',
        'pydoc',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,  # 开启压缩存档
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='QuickDaily',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # 尽可能减小体积
    upx=True,    # 使用 UPX 压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # GUI 程序不显示终端
    icon='assets/icon.ico',
)

