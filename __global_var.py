"""
This file holds global variables used in multiple files of the program

"""


from pyA20.gpio import port
from .util import lcd_driver


lcd = lcd_driver.LCD_Driver()

#left_button = port.PA20
#middle_button = port.PA14
#right_button = port.PA10

left_button = port.PA16
middle_button = port.PA14
right_button = port.PA15
