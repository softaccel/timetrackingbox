from smbus import SMBus
from time import sleep

LCD_CMD_MODE = 0
LCD_DATA_MODE = 1

# Commands
LCD_CLEAR_DISPLAY = 0x01
LCD_RETURN_HOME = 0x02
LCD_ENTRY_MODE = 0x04
LCD_DISPLAY_CTRL = 0x08
LCD_SHIFT = 0x10
LCD_FUNCTION_SET = 0x20
LCD_SET_CGRAM = 0x40
LCD_SET_DDRAM = 0x80

# Entry mode args
ENTRY_MODE_RIGHT = 0x02
ENTRY_MODE_LEFT = 0x00
ENTRY_MODE_SHIFT_DISPLAY = 0x01

# Display control args
DISPLAY_CTRL_ON = 0x04
DISPLAY_CTRL_OFF = 0x00
DISPLAY_CTRL_CURSOR_ON = 0x02
DISPLAY_CTRL_CURSOR_OFF = 0x00
DISPLAY_CTRL_BLINK_ON = 0x01
DISPLAY_CTRL_BLINK_OFF = 0x00

# Shift display args
SHIFT_LEFT = 0x00
SHIFT_RIGHT = 0x04
SHIFT_CURSOR = 0x00
SHIFT_DISPLAY = 0x08

# Function args
FUNCTION_SET_8BIT = 0x10
FUNCTION_SET_4BIT = 0x00
FUNCTION_SET_2LINE = 0x08
FUNCTION_SET_1LINE = 0x00
FUNCTION_SET_5x11_DOTS = 0x04
FUNCTION_SET_5x8_DOTS = 0x00

LCD_BACKLIGHT_ON = 0x08
LCD_BACKLIGHT_OFF = 0x00

ENABLE_BIT = 0b00000100
READ_WRITE = 0b00000010
REGIST_SEL = 0b00000001

# Line addresses
LCD_LINES = [0x80, 0xC0, 0x94, 0xD4]


class LCD_Driver:
    """
    Driver class for the LCD Display

    """

    def __init__(self):
        """
        Initializes the LCD module and sends start-up instructions:

        - Clear display * 3
        - Return home
        - Set entry mode
        - Switch display on
        - Set display parameters
        - Clear display

        """

        self.addr = 0x27
        self.bus = SMBus(0)

        self.__backlight = LCD_BACKLIGHT_ON

        self.__send(0x33)
        self.__send(0x32)
        self.__send(LCD_ENTRY_MODE | ENTRY_MODE_RIGHT)
        self.__send(LCD_DISPLAY_CTRL | DISPLAY_CTRL_ON)
        self.__send(LCD_FUNCTION_SET | FUNCTION_SET_2LINE | FUNCTION_SET_4BIT | FUNCTION_SET_5x8_DOTS)
        self.__send(LCD_CLEAR_DISPLAY)

        sleep(.0005)
    

    def __write_to_bus(self, data):
        """
        Write data to SPI bus, then wait

        """

        self.bus.write_byte(self.addr, data)
        sleep(.0001)


    def __latch(self, data):
        """
        Execute a latch operation

        """

        self.__write_to_bus( data | ENABLE_BIT )
        sleep(.0005)

        self.__write_to_bus( data & ~ENABLE_BIT )
        sleep(.0005)
    

    def __send_4_bits(self, data):
        self.__write_to_bus(data | self.__backlight)
        self.__latch(data | self.__backlight)
    

    def __send(self, data, mode = LCD_CMD_MODE):
        """
        Sends 8 bits of data, the first 4 then the last 4

        Parameters
        ----------

        data : int
            data to be sent
        
        mode : LCD_CMD_MODE / LCD_DATA_MODE:
            mode = LCD_CMD_MODE => data is a command
            mode = LCD_DATA_MODE => data is to be displayed
        
        """

        self.__send_4_bits(mode | (data & 0xF0))
        self.__send_4_bits(mode | ((data << 4) & 0xF0))


    def switchOn(self):
        self.__backlight = LCD_BACKLIGHT_ON

        self.__send(0)


    def switchOff(self):
        self.__backlight = LCD_BACKLIGHT_OFF

        self.__send(0)

    
    def clear(self):
        self.__send(LCD_CLEAR_DISPLAY)
        self.__send(LCD_RETURN_HOME)


    def PrintLine(self, text, line = 1):
        if line > 4:
            return False
        
        self.__send(LCD_LINES[line - 1])

        i = 0
        while i < len(text):
            c = ord(text[i])

            if text[i] == '&':
                if text[i + 1] != '&':
                    i += 1
                    code_fin = text[i: ].find('&')

                    c = int(text[i: i + code_fin])
                    i = i + code_fin
                else:
                    i += 2
            
            self.__send(c, LCD_DATA_MODE)
            i += 1
    

    def Print(self, lines):
        for line_nr, line_text in enumerate(lines):
            self.PrintLine(line_text, line_nr + 1)


    def LoadCustom(self, font_data):
        self.__send(LCD_SET_CGRAM)

        for line in font_data:
            for el in line:
                self.__send(el, LCD_DATA_MODE)


