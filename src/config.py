#!/usr/bin/env python3
import os
import pathlib
import tkinter as tk
from tkinter import filedialog


class Config:
    defaultPassword: str
    path: pathlib.Path
    format: str
    icon: str
    twoFASPath: str

    def __init__(self, path: pathlib.Path):
        self.defaultPassword = ""
        self.updateMenuInterval = 5
        self.path = path
        self.set_defaults(select2FASFile=False)
        self.load()

    def load(self):
        # check if file exists
        if not self.path.is_file():
            self.set_defaults()
            self.save()
            return
        with open(self.path, "r") as f:
            data = f.read()
            f.close()

        for line in data.split("\n"):
            if not line:
                continue
            key, value = line.split("=")
            if hasattr(self, key):
                setattr(self, key, value)
        if not self.twoFASPath:
            self.twoFASPath = open_file_selector()
            self.save()

    def set_defaults(self, select2FASFile=True):
        self.icon = "color"
        self.format = "{name} - {account}"
        self.defaultPassword = ""
        self.twoFASPath = ""
        self.updateMenuInterval = 5
        if select2FASFile:
            self.twoFASPath = open_file_selector()

    def save(self):
        try: os.mkdir(self.path.parent)
        except FileExistsError: pass
        with open(self.path, "w") as f:
            f.write(f"icon={self.icon}\n")
            f.write(f"twoFASPath={self.twoFASPath}\n")
            f.write(f"format={self.format}\n")
            f.write(f"defaultPassword={self.defaultPassword}\n")
            f.write(f"updateMenuInterval={self.updateMenuInterval}\n")
            f.close()


def open_file_selector():
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana de Tkinter
    file_path = filedialog.askopenfilename()  # Abrir el selector de archivos
    root.quit()
    return file_path
