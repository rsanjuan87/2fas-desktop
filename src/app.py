#!/usr/bin/env python3

import logging
import os
import pathlib
import signal
import subprocess
import sys
import threading
import time

import lib2fas
import pystray
from PIL import Image
from pystray import Menu, MenuItem

from src import config
from src.ServiceMenuItem import ServiceMenuItem, time_until_cycle

here = pathlib.Path(__file__).parent.parent

app_name = "2FAS Desktop"


class TwoFactorDesktop(object):
    def __init__(self):
        self.updater: threading.Thread | None = None
        self.do_update = True
        self.conf = None
        self.showing_notice = None
        self.services = None
        self.icon: pystray.Icon = None
        self.initialization()

    def initialization(self) -> None:
        self.updater = None
        self.do_update = True
        self.conf = config.Config(pathlib.Path.home() / ".config" / "2fas-desktop.conf")
        self.showing_notice = False
        logging.info("Loading tokens")
        self.services = lib2fas.load_services(pathlib.Path(self.conf.twoFASPath))
        self.icon = pystray.Icon(app_name, icon=self.load_logo())
        self.draw_menu()

    def draw_menu(self) -> None:
        menu_items = [
            MenuItem(draw_timer, None, enabled=False),
            Menu.SEPARATOR,
        ]

        for entry in self.services.all():
            menu_items.append(ServiceMenuItem(entry, self.notify, self.conf.format))

        trayConfig = MenuItem(
            'IconTray',
            Menu(
                MenuItem('Color', self.setTrayIconColor),
                MenuItem('White', self.setTrayIconWhite),
                MenuItem('Black', self.setTrayIconBLack),
                MenuItem('Grey', self.setTrayIconGrey),
                MenuItem('Auto', self.setTrayIconAuto),
            )
        ),
        set2FASFile = MenuItem('Set 2FAS file …', self.set2FASFile)

        self.icon.menu = Menu(
            *menu_items,
            pystray.Menu.SEPARATOR,
            MenuItem(
                'Settings',
                Menu(
                    *trayConfig,
                    set2FASFile
                )
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.stop),
        )

    def redraw_thread(self):
        """
        pystray needs this to refresh the timer, it'll only redraw the menu (updating the string)
        when update_menu is called. Seems to be okay to call it from a separate thread
        """
        logging.info("starting update thread")
        time.sleep(1)
        while self.do_update:
            time.sleep(1)
            self.draw_menu()
            self.icon.update_menu()
        logging.info("ending update thread")

    def notify(self, message):
        if self.showing_notice:
            self.icon.remove_notification()
        self.showing_notice = True
        self.icon.notify(message, app_name)

    def run(self):
        logging.info("Running update thread")
        self.do_update = True
        self.updater = threading.Thread(name="updater", target=self.redraw_thread)
        self.updater.start()
        logging.info("Running tray icon")
        self.icon.run()
        logging.info("Shutting down")

    def stop(self):
        logging.info("Stopping")
        self.do_update = False
        threading.Thread(name="icon", target=lambda: self.clean, daemon=True).start()
        time.sleep(1)
        os.kill(os.getpid(), signal.SIGINT)

    def clean(self):
        self.icon.icon = None
        self.icon.menu = None
        self.icon.update_menu()
        self.icon.stop()
        self.updater.join()

    def load_logo(self):
        try:
            image = Image.open(here / "tray" / (self.conf.icon + ".png"))
        except FileNotFoundError:
            image = Image.open(here / "tray" / "color.png")
            self.conf.icon = "color"
            self.conf.save()
        return image

    def setTrayIconColor(self) -> None:
        self.setTrayIcon('color')

    def setTrayIconWhite(self) -> None:
        self.setTrayIcon('white')

    def setTrayIconBLack(self) -> None:
        self.setTrayIcon('black')

    def setTrayIconGrey(self) -> None:
        self.setTrayIcon('grey')

    def setTrayIconAuto(self) -> None:
        self.setTrayIcon('auto')

    def setTrayIcon(self, param):
        self.conf.icon = param
        self.conf.save()
        self.draw_menu()
        self.icon.icon = self.load_logo()

    def set2FASFile(self):
        self.conf.twoFASPath = ""
        self.conf.save()
        subprocess.Popen([sys.executable] + sys.argv)
        self.stop()
        # self.icon.menu = None
        # self.initialization()
        # self.draw_menu()
        # self.run()
        # threading.Thread(name="menu", target=lambda: self.redraw_thread(), daemon=True).start()


def draw_timer(item) -> str:
    return f"Time left: {time_until_cycle():0.2f}"
