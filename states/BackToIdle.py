from Spalek.states import Idle

from Spalek import util
from Spalek.common.code import State
from Spalek.common import config
from Spalek.__global_var import lcd


class BackToIdle(State):
    def __init__(self, msg):
        self.timeout = 1
        
        if msg == "":
            self.timeout = 0

        lcd.clear()

        lines = msg.split("\n")
        for i, line in enumerate(lines):
            lcd.PrintLine(f"{line:^20}", 2 + i)

        super().__init__()
    
    
    def run(self):
        from time import sleep

        sleep(self.timeout)
        return ""
    

    def on_event(self, e):
        return Idle.Idle()
