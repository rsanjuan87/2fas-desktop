import logging
import time

import pyperclip
import pystray


class ServiceMenuItem(pystray.MenuItem):
    def __init__(self, entry, notify, formatter="{name} - {account}", ):
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
            self.notify("Wait ... Hold up")
            time.sleep(t)
        code = self.entry.generate()
        pyperclip.copy(code)
        self.notify(f"Copied {code} for {name}")


def time_until_cycle() -> float:
    now = time.time()
    time_left = 30.0 - (now % 30.0)
    return time_left
