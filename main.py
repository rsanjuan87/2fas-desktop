# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import logging
import pathlib
import sys

from src import config
from src.app import TwoFactorDesktop

app: TwoFactorDesktop
conf = config.Config

if __name__ == "__main__":
    logging.basicConfig(
        filename=pathlib.Path.home() / "2fas-desktop.log",
        filemode="w",
        encoding="utf-8",
        level=logging.DEBUG,
    )
    logging.info("Create app")
    app = TwoFactorDesktop()

    if sys.platform == "darwin":
        try:
            import objc
            from AppKit import NSApplication, NSApplicationActivationPolicyAccessory

            NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        except ImportError:
            logging.warning("PyObjC no está instalado. El icono del Dock no se ocultará.")

    app.run()
    logging.info("Done running")
    sys.exit()
