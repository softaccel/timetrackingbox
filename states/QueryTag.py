from Spalek.states import QueryProjects, EndWork, BackToIdle

from Spalek import util
from Spalek.common.code import State
from Spalek.common import config
from Spalek.__global_var import lcd

import requests


class QueryTag(State):
    def __init__(self, tagID):
        lcd.clear()
        lcd.PrintLine(f"{config.locale['PROC']:^20}", 2)

        self.__tagID = tagID

        super().__init__()


    def run(self):
        try:
            return requests.get(f"http://{config.serverIP}:{config.serverPort}/{self.__tagID}", timeout=config.timeout)
        except requests.exceptions.ConnectTimeout:
            return "TIME_OUT"
        except requests.ConnectionError:
            return "CONN_ERR"


    def on_event(self, e):
        if e == "TIME_OUT":
            return BackToIdle.BackToIdle(config.locale["REQ_TO"])

        if e == "CONN_ERR":
            return BackToIdle.BackToIdle(config.locale["SRV_UNREACH"])

        if not e:           
            if e.status_code == 500:
                return BackToIdle.BackToIdle(config.locale["SRV_INT"])

            if e.status_code == 404:
                return BackToIdle.BackToIdle(config.locale["INVALID"])
            
        if e.status_code == 202:
            return QueryProjects.QueryProjects(self.__tagID)
        
        return EndWork.EndWork(e.json(), self.__tagID)

