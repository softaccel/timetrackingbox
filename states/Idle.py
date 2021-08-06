from Spalek.states.QueryTag import QueryTag
from Spalek.util.tag_reader import RDM6300
from Spalek.common.code import State
from Spalek.common import config
from Spalek.__global_var import lcd
from datetime import datetime


class Idle(State):
    def __init__(self):
        lcd.clear()

        self.__reader = RDM6300('/dev/ttyS1', 9600)
        self.__reader.readTag()

        self.__dots = 0
        self.__fillChar = "."
        self.__last_update = datetime.now()

        super().__init__(30)


    def run(self):
        if self.__reader.done():
            return "OK"

        footer = "Spalek"

        lcd.Print([
            datetime.now().strftime("%a, %d.%m  %H:%M:%S"),
            f"{config.locale['SCAN']}" + self.__fillChar * self.__dots,
            "",
            f"{footer: >20}"
        ])

        if (datetime.now() - self.__last_update).seconds >= .9:
            self.__dots += 1

            if self.__dots > 4:
                if self.__fillChar == " ":
                    self.__fillChar = "."
                    self.__dots = 1
                else:
                    self.__fillChar = " "
                    self.__dots = 4

            self.__last_update = datetime.now()

        return "Not done"
    

    def on_event(self, e):
        if e == "TIME_OUT":
            lcd.switchOff()

            return self

        if e == "OK":
            lcd.switchOn()

            return QueryTag(self.__reader.tagID)
        return self

