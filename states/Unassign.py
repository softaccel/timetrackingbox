from Spalek.states.BackToIdle import BackToIdle

from Spalek import util
from Spalek.common.code import State
from Spalek.common import config
from Spalek.__global_var import lcd

import requests


class Unassign(State):
    def __init__(self, tagID):
        lcd.clear()
        lcd.PrintLine(f"{config.locale['PROC']:^20}", 2)

        self.__tagID = tagID

        super().__init__()


    def run(self):
        try:
            return requests.post(f"http://{config.serverIP}:{config.serverPort}/{self.__tagID}", timeout=config.timeout)
        except requests.exceptions.ConnectTimeout:
            return "TIME_OUT"


    def on_event(self, e):
        if e == "TIME_OUT":
            return BackToIdle(config.locale["REQ_TO"])
        
        if not e:
            if e.status_code == 500:
                return BackToIdle(e.text)

            if e.status_code == 404: # Should not be able to get here
                return BackToIdle(config.locale["INVALID"])
            
        return BackToIdle(config.locale["PROJ_UA"])

