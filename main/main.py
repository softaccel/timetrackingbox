from Spalek.machine import Idle
from Spalek.__global_var import lcd
from datetime import datetime
import socket
from time import sleep

if __name__ == "__main__":

    hostname = socket.gethostname()
    ip_addr = str(socket.gethostbyname(hostname))
    
    lcd.Print([hostname,"",ip_addr,""])
    sleep(5)

    state = Idle()

    try:
        while True:
            if (datetime.now() - state.startTime).seconds >= state.timeout_seconds:
                state = state.on_event("TIME_OUT")

            state = state.on_event(state.run())
    except KeyboardInterrupt:
        lcd.clear()
        lcd.switchOff()

