from Spalek.states import SelectProject, BackToIdle

from Spalek import util
from Spalek.common.code import State
from Spalek.common import config
from Spalek.__global_var import lcd

import requests


class QueryProjects(State):
    def __init__(self, tagID):
        self.__tagID = tagID

        super().__init__()


    def run(self):
        try:
            return requests.get(f"http://{config.serverIP}:{config.serverPort}/{self.__tagID}/projects", timeout=config.timeout)
        except requests.exceptions.ConnectTimeout:
            return "TIME_OUT"
    

    def on_event(self, e):
        if e == "TIME_OUT":
            return BackToIdle.BackToIdle(config.locale["REQ_TO"])
        
        if not e:
            if e.status_code == 500:
                return BackToIdle.BackToIdle(config.locale["SRV_INT"])

            if e.status_code == 404: # Should not be able to get here
                return BackToIdle.BackToIdle(config.locale["INVALID"])
            
        if e.status_code == 202:
            return BackToIdle.BackToIdle(config.locale["NO_PROJ"])
        
        return SelectProject.SelectProject(e.json(), self.__tagID)
    
