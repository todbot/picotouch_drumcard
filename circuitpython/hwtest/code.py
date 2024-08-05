# SPDX-FileCopyrightText: Copyright (c) 2024 Tod Kurt
# SPDX-License-Identifier: MIT
"""
picotouch_drumcard_hwtest.py --
31 Jul 2024 - @todbot / Tod Kurt
Part of https://github.com/todbot/picotouch_drumcard
"""

import time, random
import board
import busio
import pwmio
import usb_midi
import tmidi
import ts20

# fmt: off
led_pins = (
    board.GP2, board.GP3, board.GP4, board.GP5,
    board.GP27, board.GP26, board.GP22, board.GP21,
    board.GP6, board.GP7, board.GP8, board.GP9,
    board.GP14, board.GP19, board.GP20
)
# fmt: on

i2c_sda_pin = board.GP16
i2c_scl_pin = board.GP17
midi_out_pin = board.GP0
midi_in_pin = board.GP1

i2c = busio.I2C(scl=i2c_scl_pin, sda=i2c_sda_pin)
ts20 = ts20.TS20(i2c)

uart = busio.UART(tx=midi_out_pin, rx=midi_in_pin, baudrate=31250, timeout=0.0001)
midi_usb = tmidi.MIDI(midi_in=usb_midi.ports[0], midi_out=usb_midi.ports[1])
midi_uart = tmidi.MIDI(midi_in=uart)

leds = []
num_leds = len(led_pins)

for pin in led_pins:
    led = pwmio.PWMOut(pin, frequency=25000, duty_cycle=0)
    leds.append(led)
    
def set_led(n, val=1.0):
    leds[n].duty_cycle = int(65535 * val)
    
def dim_all_leds(amount=0.95):
    """Dim all LEDs by an amount"""
    for led in leds:
        led.duty_cycle = int(led.duty_cycle * amount)

print("picotouch_drumcard_hwtest: startup demo")
i = 0
demo_led_map = (0,1,2,3, 8,9,10, 7,6,5,4)  # circle around clockwise
for j in range(5):
    for i in range(num_leds):
        set_led(demo_led_map[i], 1)
        dim_all_leds(0.7)
        time.sleep(0.03)

print("picotouch_drumcard_hwtest: ready")
last_time = 0
while True:
    now = time.monotonic()
    if now - last_time > 0.2:
        last_time = now
        print("hi")
        touches = ts20.read_touches()
        print(touches)

    dim_all_leds(0.95)
