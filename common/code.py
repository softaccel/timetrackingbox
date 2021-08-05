"""
This file contains code that is used in multiple files of the program

"""


from time import sleep
from pyA20.gpio import gpio
from datetime import datetime


class State(object):
    def __init__(self, maxWait = 10):
        self.startTime = datetime.now()
        self.timeout_seconds = maxWait


    def run(self):
        pass


    def on_event(self, e):
        pass


def read(button):
    state = gpio.input(button)

    sleep(.001)

    return (gpio.input(button) == state) and state
