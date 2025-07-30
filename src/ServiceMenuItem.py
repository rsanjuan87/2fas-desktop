# -*- coding: utf-8 -*-
import logging
import sys
import time

import pyperclip
import pystray

try:
    if sys.platform == "darwin":
        import pync
        import os
        import cairosvg
        # Convertir color.svg a .icns temporal si es necesario
        SVG_ICON = os.path.abspath(os.path.join(os.path.dirname(__file__), "../tray/color.svg"))
        ICNS_ICON = os.path.abspath(os.path.join(os.path.dirname(__file__), "../tray/color.icns"))
        if not os.path.exists(ICNS_ICON):
            # Convertir SVG a PNG temporal
            PNG_ICON = os.path.abspath(os.path.join(os.path.dirname(__file__), "../tray/color.png"))
            cairosvg.svg2png(url=SVG_ICON, write_to=PNG_ICON, output_width=256, output_height=256)
            # Convertir PNG a ICNS usando sips y iconutil (solo si no existe)
            import subprocess
            ICONSET_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../tray/color.iconset"))
            os.makedirs(ICONSET_DIR, exist_ok=True)
            subprocess.run(["sips", "-z", "128", "128", PNG_ICON, "--out", os.path.join(ICONSET_DIR, "icon_128x128.png")])
            subprocess.run(["iconutil", "-c", "icns", ICONSET_DIR, "-o", ICNS_ICON])
        def mac_notify(message):
            pync.notify(message, title="2FAS Desktop", appIcon=ICNS_ICON)
    else:
        mac_notify = None
except ImportError:
    mac_notify = None


class ServiceMenuItem(pystray.MenuItem):
    def __init__(self, entry, notify, formatter="{name} - {account} - {otp}", ):
        self.entry = entry
        self.notify = notify
        self.format = formatter
        self.texto = formatter
        self.texto = self.texto.replace("{name}", entry.name)
        self.texto = self.texto.replace("{secret}", entry.secret)
        self.texto = self.texto.replace("{updatedAt}", str(entry.updatedAt))
        self.texto = self.texto.replace("{serviceTypeID}", str(entry.serviceTypeID))

        self.texto = self.texto.replace("{link}", str(entry.otp.link))
        self.texto = self.texto.replace("{tokenType}", str(entry.otp.tokenType))
        self.texto = self.texto.replace("{source}", str(entry.otp.source))
        self.texto = self.texto.replace("{label}", str(entry.otp.label))
        self.texto = self.texto.replace("{account}", str(entry.otp.account))
        self.texto = self.texto.replace("{digits}", str(entry.otp.digits))
        self.texto = self.texto.replace("{period}", str(entry.otp.period))

        # if self.text.__contains__("{otp}"):
        #     try:
        #         self.text = self.text.replace("{otp}", entry.generate())
        #     except:
        #         self.text = self.text.replace("{otp}", "Error")

        super(ServiceMenuItem, self).__init__(f"{self.texto}", self.on_click)
        self._original_notify = notify

    @property
    def text(self):
        if self.texto.__contains__("{otp}"):
            try:
                return self.texto.replace("{otp}", self.entry.generate())
            except:
                return self.texto.replace("{otp}", "Error")
        else:
            return self.texto

    def on_click(self):
        name = self.entry.name
        code = self.entry.generate()
        logging.info(f"code for {name} is {code}")
        t = time_until_cycle()
        if t < 5.0:
            self._notify("Wait ... Hold up")
            time.sleep(t)
        code = self.entry.generate()
        pyperclip.copy(code)
        self._notify(f"Copied {code} for {name}")

    def _notify(self, message):
        if mac_notify:
            mac_notify(message)
        else:
            self._original_notify(message)


def time_until_cycle() -> float:
    now = time.time()
    time_left = 30.0 - (now % 30.0)
    return time_left
