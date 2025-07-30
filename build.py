# -*- coding: utf-8 -*-
from setuptools import setup

APP = ['main.py']
DATA_FILES = [
    ('tray', ['tray/color.svg', 'tray/color.icns', 'tray/black.svg', 'tray/grey.svg', 'tray/white.svg']),
    # Agrega aquí otros recursos si es necesario
]
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'tray/color.icns',
    'includes': ['cairosvg', 'pyperclip', 'pystray', 'pync'],
    'packages': [],
    'plist': {
        'CFBundleName': '2FAS Desktop',
        'CFBundleDisplayName': '2FAS Desktop',
        'CFBundleIdentifier': 'com.tuempresa.2fasdesktop',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)