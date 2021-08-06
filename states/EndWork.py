from Spalek.states import Unassign, BackToIdle

from Spalek import util
from Spalek.common.code import State, read
from Spalek.common import config
from Spalek.__global_var import lcd, left_button, right_button, middle_button


class EndWork(State):
    def __init__(self, project, tagID):
        lcd.clear()
        lcd.Print([
            config.locale["STOP"],
            f"{project['text']}{project['time']: >{17 - len(project['text'])}}min",
            "",
            f"OK{config.locale['BACK']: >18}"
        ])

        self.__last_states = [0, 0, 0]

        self.__tagID = tagID

        super().__init__()
    

    def run(self):
        from time import sleep

        left_pressed = not read(left_button)
        right_pressed = not read(right_button)

        if left_pressed and left_pressed != self.__last_states[0]:
            return "OK"

        if right_pressed and right_pressed != self.__last_states[2]:
            return "CANCEL"

        self.__last_states[0] = left_pressed
        self.__last_states[2] = right_pressed
        
        return "WAIT"


    def on_event(self, e):
        if e == "TIME_OUT":
            return BackToIdle.BackToIdle("")
        
        if e == "WAIT":
            return self
        
        if e == "CANCEL":
            return BackToIdle.BackToIdle(config.locale["CANCELED"])
        
        return Unassign.Unassign(self.__tagID)
