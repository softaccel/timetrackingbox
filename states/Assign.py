from Spalek.states.BackToIdle import BackToIdle

from Spalek import util
from Spalek.common.code import State
from Spalek.common import config
from Spalek.__global_var import lcd

import requests


class Assign(State):
    def __init__(self, project, tagID):
        self.__projectID = project["ID"]

        self.__tagID = tagID

        super().__init__()
    
    
    def run(self):
        try:
            return requests.post(f"http://{config.serverIP}:{config.serverPort}/{self.__tagID}", json={"projectID" : self.__projectID}, timeout=config.timeout)
        except requests.exceptions.ConnectTimeout:
            return "TIME_OUT"


    def on_event(self, e):
        if e == "TIME_OUT":
            return BackToIdle(config.locale["REQ_TO"])
        
        if not e:
            if e.status_code == 500:
                return BackToIdle(config.locale["SRV_INT"])

            if e.status_code == 404: # Should not be able to get here
                return BackToIdle(config.locale["INVALID"])
        
        return BackToIdle(config.locale["PROJ_A"])
    
