import logging
import time

import pyperclip
import pystray


class ServiceMenuItem(pystray.MenuItem):
    def __init__(self, entry, notify, formater="{name} - {account}", ):
        self.entry = entry
        self.notify = notify
        f = formater
        f = f.replace("{name}", entry.name)
        f = f.replace("{secret}", entry.secret)
        f = f.replace("{updatedAt}", str(entry.updatedAt))
        f = f.replace("{serviceTypeID}", str(entry.serviceTypeID))

        f = f.replace("{link}", str(entry.otp.link))
        f = f.replace("{tokenType}", str(entry.otp.tokenType))
        f = f.replace("{source}", str(entry.otp.source))
        f = f.replace("{label}", str(entry.otp.label))
        f = f.replace("{account}", str(entry.otp.account))
        f = f.replace("{digits}", str(entry.otp.digits))
        f = f.replace("{period}", str(entry.otp.period))

        if f.__contains__("{otp}"):
            f = f.replace("{otp}", entry.generate())

        super(ServiceMenuItem, self).__init__(f"{f}", self.on_click)

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
