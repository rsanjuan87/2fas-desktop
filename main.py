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
    app.run()
    logging.info("Done running")
    sys.exit()
