#!/usr/bin/env python3
import io
import logging
import os
import pathlib
import signal
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import simpledialog, messagebox

import lib2fas
import pyjson5.pyjson5
import pystray
from PIL import Image
from pystray import Menu, MenuItem

from src import config
from src.ServiceMenuItem import ServiceMenuItem, time_until_cycle

gtkbin = r'C:\Program Files\GTK3-Runtime Win64\bin'
add_dll_dir = getattr(os, 'add_dll_directory', None)
if callable(add_dll_dir):
    add_dll_dir(gtkbin)
else:
    os.environ['PATH'] = os.pathsep.join((gtkbin, os.environ['PATH']))
import cairosvg

here = pathlib.Path(__file__).parent.parent

app_name = "2FAS Desktop"


class TwoFactorDesktop(object):
    def __init__(self):
        self.otp_menu_items = []
        self.otp_menu = None
        self.trayConfig = MenuItem(
            'IconTray',
            Menu(
                MenuItem('Color', self.setTrayIconColor, checked=lambda item: self.conf.icon == 'color'),
                MenuItem('White', self.setTrayIconWhite, checked=lambda item: self.conf.icon == 'white'),
                MenuItem('Black', self.setTrayIconBLack, checked=lambda item: self.conf.icon == 'black'),
                MenuItem('Grey', self.setTrayIconGrey, checked=lambda item: self.conf.icon == 'grey'),
                MenuItem('Auto', self.setTrayIconAuto, checked=lambda item: self.conf.icon == 'auto'),
            )
        ),
        self.setDefaultPass = MenuItem('Set default pass …', self.setDefaultPass)
        self.set2FASFile = MenuItem('Set 2FAS file …', self.set2FASFileClick)
        self.menu_items = [
            MenuItem(draw_timer, None, enabled=False),
            Menu.SEPARATOR,

            pystray.Menu.SEPARATOR,
            MenuItem(
                'Settings',
                Menu(
                    *self.trayConfig,
                    self.set2FASFile,
                    self.setDefaultPass,
                )
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.stop),
        ]

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
        password = self.conf.defaultPassword
        gotError = True
        if self.conf.twoFASPath is not None and self.conf.twoFASPath != "" and pathlib.Path(
                self.conf.twoFASPath).is_file():
            while gotError:
                try:
                    self.services = lib2fas.load_services(pathlib.Path(self.conf.twoFASPath), passphrase=password)
                    gotError = False
                except PermissionError:
                    if password != "":
                        messagebox.showerror("Invalid Password", "The password entered is invalid. Please try again.")
                    password = prompt_password_gui("Password: ")
                    if password is None:
                        gotError = False
                except pyjson5.pyjson5.Json5IllegalCharacter:
                    messagebox.showerror("Invalid File", "The file selected is not a valid 2FAS file.")
                    self.conf.twoFASPath = ""
                    self.conf.save()
                    self.set2FASFileClick()
                    gotError = False
                    self.initialization()

        self.icon = pystray.Icon(app_name, icon=self.load_logo())
        self.draw_menu()

    def draw_menu(self) -> None:

        if self.services is not None:
            self.otp_menu_items = [
                # MenuItem(draw_timer, None, enabled=False),
                # MenuItem("<- Back", self.setMenuMain),

            ]
            for entry in self.services.all():
                # otp_menu_items.append(ServiceMenuItem(entry, self.notify, self.conf.format))
                self.otp_menu_items.append(ServiceMenuItem(entry, self.notify, self.conf.format))

            # self.otp_menu = Menu(*otp_menu_items)
        # otp_menu_item = MenuItem(
        #     "Services",
        #     self.otp_menu,
        #     # self.setMenuOtp,
        # )

        self.icon.menu = [
            # Menu(
            *self.menu_items[0:2],
            # Menu.SEPARATOR,
            *self.otp_menu_items,
            # Menu.SEPARATOR,
            *self.menu_items[2:],
            # )
        ]

    def switchMenu(self):
        if self.icon.menu == self.otp_menu:
            self.setMenuMain()
        else:
            self.setMenuOtp()

    def setMenuOtp(self):
        self.icon.menu = self.otp_menu
        self.icon.update_menu()

    def setMenuMain(self):
        self.icon.menu = Menu(
            *self.menu_items,
        )
        self.icon.update_menu()

    def redraw_thread(self):
        """
        pystray needs this to refresh the timer, it'll only redraw the menu (updating the string)
        when update_menu is called. Seems to be okay to call it from a separate thread
        """
        logging.info("starting update thread")
        time.sleep(1)
        while self.do_update:
            v = int(self.conf.updateMenuInterval)
            if v < 1:
                v = time_until_cycle()
                if v < 10:
                    v = 1
            time.sleep(v)
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
        time.sleep(1)
        os.kill(os.getpid(), signal.SIGTERM)
        time.sleep(1)
        os.kill(os.getpid(), signal.SIGKILL)

    def clean(self):
        self.icon.icon = None
        self.icon.menu = None
        self.icon.update_menu()
        self.icon.stop()
        self.updater.join()

    def load_logo(self):
        try:
            image = svg_to_image((here / "tray" / (self.conf.icon + ".svg")).as_uri())
        except:
            image = svg_to_image((here / "tray" / "color.svg").as_uri())
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

    def set2FASFileClick(self):
        self.conf.twoFASPath = ""
        self.conf.save()
        subprocess.Popen([sys.executable] + sys.argv)
        self.stop()
        # self.icon.menu = None
        # self.initialization()
        # self.draw_menu()
        # self.run()
        # threading.Thread(name="menu", target=lambda: self.redraw_thread(), daemon=True).start()

    def setDefaultPass(self):
        password = prompt_password_gui("Default password(NOT SECURE): ")
        if password is not None:
            self.conf.defaultPassword = password
            self.conf.save()


def draw_timer(item) -> str:
    return f"Time left: {int(time_until_cycle())} sec"


def prompt_password_gui(prompt="Password: ") -> str | None:
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    password = simpledialog.askstring("Password Input", prompt, show='*')
    root.quit()  # Clean up root window
    return password


def svg_to_image(svg_path: str) -> Image.Image:
    # Convertir SVG a PNG en memoria
    png_data = cairosvg.svg2png(url=svg_path, output_height=32, output_width=32)
    # Cargar PNG desde datos en memoria
    image = Image.open(io.BytesIO(png_data))
    return image
