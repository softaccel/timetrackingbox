"""
This file contains the definitions of the state machine's states

"""


from Spalek.util.tag_reader import RDM6300

from Spalek.common.code import State, read
from Spalek.common import config

from Spalek.__global_var import lcd, left_button, right_button, middle_button

from datetime import datetime
import requests
import logging


class Idle(State):
    """
    Idle State: initial state

    In this state, the machine waits for tags.
    After a tag is presented and read, it sends the tag's id
    to the QueryTag state

    Events
    ==============
        "TIME_OUT" : occurs after a period of inactivity, switches display off
        "OK" : tag read successfully, switches display on and calls the next state: QueryTag

        Otherwise returns self

    """


    def __init__(self):
        """
        Initilizes tag reader with the /dev/ttyS1 serial port and a baud rate of 9600 BPS

        Timeout after 30 seconds

        """

        lcd.clear()

        self.__reader = RDM6300('/dev/ttyS1', 9600)
        self.__reader.readTag()

        self.__dots = 0
        self.__fillChar = "."
        self.__last_update = datetime.now()

        super().__init__(30)


    def run(self):
        """
        Print current date and time on first line, a message on line 2 and a footer on line 4

        """

        try:
            if self.__reader.done():
                return "OK"
        except Exception as e:
            print(str(e))

            logging.warning("TAG_READER: " + str(e))
            self.__reader.readTag()

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

        return "WAIT"
    

    def on_event(self, e):
        if e == "TIME_OUT":
            lcd.switchOff()

            return self

        if e == "OK":
            lcd.switchOn()
            id = self.__reader.tagID

            del self.__reader

            return QueryTag(id)
        return self


class QueryTag(State):
    """
    Make a call to the API requesting information about the read tag

    Events
    ==============
        "TIME_OUT" : Request timed out, calls BackToIdle with the corresponding message
        "CONN_ERR" : Connection error: server unreachable or error occurred during processing

        Otherwise checks status code and responds appropriately
    
    Status codes
    ==============
        200 : A project was assigned, calls EndWork to end it
        202 : No project is assigned, calls QueryProjects to get a list of assignable projects
        404 : Invalid or unrecognised tag
        500 : Internal server error

    """

    def __init__(self, tagID):
        lcd.clear()
        lcd.PrintLine(f"{config.locale['PROC']:^20}", 2)

        self.__tagID = tagID

        super().__init__()


    def run(self):
        """
        Makes a call to the API to get the status of the read tag

        """

        try:
            resp = requests.get(f"{serverIP}/tags/{self.__tagID}", timeout=config.timeout)

            if not resp:
                return 500

            if resp.json()["data"] is None:
                return "INVALID"
            
            # Tag is valid
            resp = requests.get(f"{serverIP}/tags/{self.__tagID}/started_work", timeout=config.timeout)

            if not resp:
                return 500
            
            return resp.json()["data"]

        except requests.exceptions.ConnectTimeout:
            return "TIME_OUT"
        
        except requests.ConnectionError:
            return "CONN_ERR"


    def on_event(self, e):
        if e == "TIME_OUT":
            return BackToIdle(config.locale["REQ_TO"])

        if e == "CONN_ERR":
            return BackToIdle(config.locale["SRV_UNREACH"])
        
        if e == "INVALID":
            return BackToIdle(config.locale["INVALID"])
        
        if e == 500:
            return BackToIdle(config.locale["SRV_INT"])
            
        if not e:
            return QueryProjects(self.__tagID)
        
        return EndWork(self.__tagID, e[0])


class QueryProjects(State):
    """
    Makes a call to the API to get a list of projects related to the tag.

    Events
    ==============
        "TIME_OUT" : Request timed out, return to Idle and display error message
        "CONN_ERR" : Connection error: server unreachable or error occurred during processing

        Otherwise checks status code and responds appropriately    
    
    Status codes
    ==============
        200 : OK, calls AcceptProject if there is only one record in the list, or passes the whole list to SelectProject
        202 : No assignable projects
        404 : Invalid or unrecognised tag - should not be able to reach this point after getting through QueryTag
        500 : Internal server error

    """

    def __init__(self, tagID):
        self.__tagID = tagID

        super().__init__()


    def run(self):
        try:
            resp = requests.get(f"{serverIP}/tags/{self.__tagID}/alloc_orders")

            if not resp:
                return 500
            
            return resp.json()["data"]

        except requests.exceptions.ConnectTimeout:
            return "TIME_OUT"
        
        except requests.ConnectionError:
            return "CONN_ERR"
    

    def on_event(self, e):
        if e == "TIME_OUT":
            return BackToIdle(config.locale["REQ_TO"])
        
        if e == "CONN_ERR":
            return BackToIdle(config.locale["SRV_UNREACH"])
        
        if e == 500:
            return BackToIdle(config.locale["SRV_INT"])
        
        if not e:
            return BackToIdle(config.locale["NO_PROJ"])
        
        fname = e[0]["attributes"]["fname"]
        lname = e[0]["attributes"]["lname"]

        display_name = f"{fname[0]}. {lname}"[0:19]

        if len(e) == 1:
            return AcceptProject(e[0], self.__tagID, display_name)
        
        return SelectProject(e, self.__tagID, display_name)


class AcceptProject(State):
    """
    Prompts the user to start a project or cancel the action.

    Events
    ==============
        "TIME_OUT" : User has been idle for too long, return to Idle state
        "WAIT" : No input from user, returns self
        "CANCEL" : User canceled the action, goes to BackToIdle with a confiramtion of the cancellation

        Otherwise the user chose to start the project, returns Assign
    
    """


    def __init__(self, project, tagID, tagUser):
        """
        Clears the display and prints the menu

        """

        lcd.clear()

        project = project["attributes"]
        proj_text = f"{project['order_name']} {project['op_name']}"[0:17]

        lcd.Print([
            f"{tagUser: >20}",
            f"&0& {proj_text} &1&",
            "",
            f"OK{config.locale['BACK']: >18}"
        ])

        self.__project = project
        self.__tagID = tagID
        self.__last_states = [0, 0, 0] # Initial button states (not pressed) : left, middle, right
        
        super().__init__()

    
    def run(self):
        left_pressed = not read(left_button)
        middle_pressed = not read(middle_button)
        right_pressed = not read(right_button)

        if left_pressed and left_pressed != self.__last_states[0]:
            return self.__project

        if right_pressed and right_pressed != self.__last_states[2]:
            return "CANCEL"

        self.__last_states[0] = left_pressed
        self.__last_states[1] = middle_pressed
        self.__last_states[2] = right_pressed
        
        return "WAIT"


    def on_event(self, e):
        if e == "TIME_OUT":
            return BackToIdle("")
        
        if e == "WAIT":
            return self
        
        if e == "CANCEL":
            return BackToIdle(config.locale["CANCELED"])
        
        return Assign(e, self.__tagID)


class SelectProject(State):
    """
    Prompts the user to select a project or cancel the action.

    Events
    ==============
        "TIME_OUT" : User has been idle for too long, return to Idle state. Pressing a button resets the timer
        "WAIT" : No input from user, returns self

        Otherwise : - if the user chose to start a project, returns Assign
                    - if the user chose to cancel, returns BackToIdle with a confirmation of the cancellation
    
    """


    def __init__(self, projects, tagID, tagUser):
        """
        Clears display and prints the header and footer
        
        """

        lcd.clear()

        self.__projects_list = projects
        self.__tagID = tagID
        self.__tagUser = tagUser

        self.__projects_list.append({"attributes": {"id": -1, "order_name": config.locale["BACK"]}})
        self.__projects_list.extend(self.__projects_list)

        self.__last_states = [0, 0, 0]  # Initial button states (not pressed) : left, middle, right
        self.__selected = 0

        lcd.PrintLine(f"{self.__tagUser: >20}", 1)       # Header
        # lcd.PrintLine("OK       &3&         &2&", 4)     # Footer
        lcd.PrintLine("OK                 &2&", 4)     # Footer

        super().__init__()

    
    def run(self):

        # Print two of the projects from the list

        topProject = f"&0& {get_display_text(self.__projects_list[self.__selected]['attributes'])} &1&"

        listToPrint = ["", f"{topProject:20}"]
        listToPrint.extend(
            [f"  {get_display_text(p['attributes']): <18}" for p in self.__projects_list[(self.__selected + 1):(self.__selected + 2)]]
        )

        lcd.Print(listToPrint)

        # Check for button action

        left_pressed = not read(left_button)
        # middle_pressed = not read(middle_button)
        right_pressed = not read(right_button)

        if left_pressed and left_pressed != self.__last_states[0]:
            return self.__projects_list[self.__selected]

        # if middle_pressed and middle_pressed != self.__last_states[1]:
        #     self.startTime = datetime.now()
        #     self.__selected -= 1

        #     if self.__selected < 0:
        #         self.__selected = int(len(self.__projects_list) / 2) - 1

        if right_pressed and right_pressed != self.__last_states[2]:
            self.startTime = datetime.now()
            self.__selected += 1

            if self.__selected >= len(self.__projects_list) / 2:
                self.__selected = 0

        self.__last_states[0] = left_pressed
        # self.__last_states[1] = middle_pressed
        self.__last_states[2] = right_pressed
        
        return "WAIT"
    

    def on_event(self, e):
        if e == "TIME_OUT":
            return BackToIdle("")

        if e == "WAIT":
            return self
        
        if e['attributes']['id'] == -1:
            return BackToIdle(config.locale["CANCELED"])
        
        return Assign(e, self.__tagID)
    

    def get_display_text(project):
        return f"{project['order_name']} {project['op_name']}"[0:17]


class Assign(State):
    """
    Makes a call to the API to start a project
    If the response is valid, returns BackToIdle with a confirmation message

    Events
    ==============
        "TIME_OUT" : Request timed out, returns BackToIdle with an error message
        "CONN_ERR" : Connection error: server unreachable or error occurred during processing

    Status codes
    ==============
        200 : OK
        404 : Invalid or unrecognised tag - should not be able to reach this point after getting through QueryTag
        500 : Internal server error

    """
    
    
    def __init__(self, project, tagID):
        self.__project = project['attributes']

        self.__tagID = tagID

        super().__init__()
    
    
    def run(self):
        try:
            req_data = {
                "data": {
                    "type": "timetracking",
                    "attributes": {
                        "hourly_rate": self.__project["hourlyrate"],
                        "employee": int(self.__project["emplid"]),
                        "operation": int(self.__project["op_id"]),
                        "order": int(self.__project["order_id"]),
                        "currency": self.__project["currency"]
                    }
                }
            }
            req_headers = {"Content-Type": "application/vnd.api+json"}

            resp = requests.post(f"{config.serverIP}/timetracking", headers=req_headers, data=json.dumps(req_data), timeout=config.timeout)

            if not resp:
                return 500

            return resp.json()['data']

        except requests.exceptions.ConnectTimeout:
            return "TIME_OUT"
        
        except requests.ConnectionError:
            return "CONN_ERR"


    def on_event(self, e):
        if e == "TIME_OUT":
            return BackToIdle(config.locale["REQ_TO"])
        
        if e == "CONN_ERR":
            return BackToIdle(config.locale["SRV_UNREACH"])
        
        if e == 500:
            return BackToIdle(config.locale["SRV_INT"])
        
        return BackToIdle(config.locale["PROJ_A"])


class EndWork(State):
    """
    Prompts the user to end the current running project or cancel the action.

    Events
    ==============
        "TIME_OUT" : User has been idle for too long, return BackToIdle
        "WAIT" : User is idle, return self
        "CANCEL" : User canceled the action, return BackToIdle with a confirmation of the cancellation

        Otherwise the user chose to stop the project, return Unassign

    """


    def __init__(self, tagID, project):
        """
        Clears the display and prints querys the user for confirmation

        """

        project = project["attributes"]
        proj_text = f"{project['order_name']} {project['op_name']}"[0:17]

        lcd.clear()
        lcd.Print([
            config.locale["STOP"],
            f"{proj_text}{project['time']: >{17 - len(project['text'])}}min",
            "",
            f"OK{config.locale['BACK']: >18}"
        ])

        self.__last_states = [0, 0, 0]  # Initial button states (not pressed) : left, middle, right

        self.__tagID = tagID

        super().__init__()
    

    def run(self):
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
            return BackToIdle("")
        
        if e == "WAIT":
            return self
        
        if e == "CANCEL":
            return BackToIdle(config.locale["CANCELED"])
        
        return Unassign(self.__tagID)


class Unassign(State):
    """
    Makes a call to the API with an empty POST to stop the current running project.

    Events
    ==============
        "TIME_OUT" : Request timed out, return BackToIdle with an error message
        "CONN_ERR" : Connection error: server unreachable or error occurred during processing

        Otherwise if the response status is ok, return BackToIdle with a confirmation message

    Status codes
    ==============
        200 : OK
        404 : Invalid or unrecognised tag - should not be able to reach this point after getting through QueryTag
        500 : Internal server error

    """

    def __init__(self, tagID):
        lcd.clear()
        lcd.PrintLine(f"{config.locale['PROC']:^20}", 2)

        self.__tagID = tagID

        super().__init__()


    def run(self):
        try:
            return requests.post(f"http://{config.serverIP}:{config.serverPort}/{self.__tagID}", timeout=config.timeout)
        except requests.exceptions.ConnectTimeout:
            return "TIME_OUT"
        except requests.ConnectionError:
            return "CONN_ERR"


    def on_event(self, e):
        if e == "TIME_OUT":
            return BackToIdle(config.locale["REQ_TO"])
        
        if e == "CONN_ERR":
            return BackToIdle(config.locale["SRV_UNREACH"])
        
        if not e:
            if e.status_code == 500:
                return BackToIdle(e.text)

            if e.status_code == 404:
                return BackToIdle(config.locale["INVALID"])
            
        return BackToIdle(config.locale["PROJ_UA"])


class BackToIdle(State):
    """
    Prints a message for `timeout` seconds then goes to the Idle state

    Events
    ==============
        "TIME_OUT" : Message was displayed for long enough, go back to Idle

        Otherwise returns self
    
    """

    def __init__(self, msg):
        """
        Clears display and prints the custom message
        
        """

        self.timeout = config.backToIdle_timeout
        
        if msg == "":
            self.timeout = 0

        lcd.clear()

        lines = msg.split("\n")
        for i, line in enumerate(lines):
            lcd.PrintLine(f"{line:^20}", 2 + i)

        super().__init__(self.timeout)
    
    
    def run(self):

        return ""
    

    def on_event(self, e):
        if e == "TIME_OUT":
            return Idle()
        
        return self


# Create and configure the logger

logging.basicConfig(filename="/root/Python/Spalek/log.txt")
logging.info("Program started")

