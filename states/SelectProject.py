from Spalek.states import Assign, BackToIdle

from Spalek import util
from Spalek.common.code import State, read
from Spalek.common import config
from Spalek.__global_var import lcd, left_button, right_button, middle_button


class SelectProject(State):
    def __init__(self, projects, tagID):
        lcd.clear()

        self.__projects_list = projects
        self.__tagID = tagID

        self.__projects_list.append({"ID": -1, "text": config.locale["BACK"]})
        self.__projects_list.extend(self.__projects_list)

        self.__last_states = [0, 0, 0]
        self.__selected = 0

        super().__init__()

    
    def run(self):
        topProject = f"&0& {self.__projects_list[self.__selected]['text']} &1&"

        listToPrint = [f"{topProject:20}"]
        listToPrint.extend(
            [f"  {p['text']: <20}" for p in self.__projects_list[(self.__selected + 1):(self.__selected + 3)]]
        )

        lcd.Print(listToPrint)
        lcd.PrintLine("  &2&     &3&       OK", 4)

        left_pressed = not read(left_button)
        middle_pressed = not read(middle_button)
        right_pressed = not read(right_button)

        if left_pressed and left_pressed != self.__last_states[0]:
            self.__selected += 1

            if self.__selected >= len(self.__projects_list) / 2:
                self.__selected = 0
        
        if middle_pressed and middle_pressed != self.__last_states[1]:
            self.__selected -= 1

            if self.__selected < 0:
                self.__selected = int(len(self.__projects_list) / 2) - 1

        if right_pressed and right_pressed != self.__last_states[2]:
            return self.__projects_list[self.__selected]

        self.__last_states[0] = left_pressed
        self.__last_states[1] = middle_pressed
        self.__last_states[2] = right_pressed
        
        return "WAIT"
    

    def on_event(self, e):
        if e == "TIME_OUT":
            return BackToIdle.BackToIdle("")

        if e == "WAIT":
            return self
        
        if e["ID"] == -1:
            return BackToIdle.BackToIdle(config.locale["CANCELED"])
        
        return Assign.Assign(e, self.__tagID)
