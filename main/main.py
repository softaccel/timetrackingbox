from Spalek.machine import Idle
from Spalek.__global_var import lcd
from datetime import datetime

state = Idle()

try:
    while True:
        if (datetime.now() - state.startTime).seconds >= state.timeout_seconds:
            state = state.on_event("TIME_OUT")

        state = state.on_event(state.run())
except KeyboardInterrupt:
    lcd.clear()
    lcd.switchOff()

