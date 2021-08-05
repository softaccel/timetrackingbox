from pyA20.gpio import gpio
from pyA20.gpio import connector

import Spalek.__global_var as G


# Setup buttons

gpio.init()

gpio.setcfg(G.left_button, gpio.INPUT)
gpio.setcfg(G.middle_button, gpio.INPUT)
gpio.setcfg(G.right_button, gpio.INPUT)

gpio.pullup(G.left_button, gpio.PULLUP)
gpio.pullup(G.middle_button, gpio.PULLUP)
gpio.pullup(G.right_button, gpio.PULLUP)

# Create and load oad custom font

fontdata1 = [
        # Arrow left
        [ 0x00, 0x04, 0x02, 0x1F, 0x02, 0x04, 0x00, 0x00 ],
        # Arrow right
        [ 0x00, 0x04, 0x08, 0x1F, 0x08, 0x04, 0x00, 0x00 ],
        # Down
        [ 0x00, 0x00, 0x00, 0x1F, 0x0E, 0x04, 0x00, 0x00 ],
        # Up
        [ 0x00, 0x00, 0x04, 0x0E, 0x1F, 0x00, 0x00, 0x00 ]
]

G.lcd.LoadCustom(fontdata1)
