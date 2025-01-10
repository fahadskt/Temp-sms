# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None
current_dir = os.path.abspath(os.path.dirname('__file__'))

a = Analysis(
    [os.path.join(current_dir, 'temp_sms_gui_tk.py')],
    pathex=[current_dir],
    binaries=[],
    datas=[
        (os.path.join(current_dir, 'tempsms.py'), '.'),
        (os.path.join(current_dir, 'requirements.txt'), '.'),
    ],
    hiddenimports=[
        'tkinter', 
        'requests', 
        'Crypto',
        'Crypto.Cipher',
        'Crypto.Cipher.AES',
        'Crypto.Util',
        'Crypto.Util.Padding',
        'pyperclip',
        'colorama',
        'pyfiglet',
        'subprocess',
        'base64',
        'os',
        'sys',
        'random',
        'time',
        'threading',
        'json',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.messagebox'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add debug prints
print("Current directory:", current_dir)
print("Data files to be included:", a.datas)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TempSMS',
    debug=True,  # Enable debug mode
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Temporarily enable console for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
