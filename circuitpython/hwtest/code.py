print("Hello World!")
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
import digitalio
import pwmio
import audiopwmio, audiomixer, audiocore, synthio
import usb_midi
import ulab.numpy as np
import tmidi
import ts20

i2c_sda_pin = board.GP16
i2c_scl_pin = board.GP17
midi_out_pin = board.GP0
midi_in_pin = board.GP1
audio_pin = board.GP28
pico_pwr_pin = board.GP23

      
# fmt: off
led_pins = (
    board.GP2, board.GP3, board.GP4, board.GP5,     # 1,2,3,4
    board.GP27, board.GP26, board.GP22, board.GP21, # 5,6,7,8
    board.GP6, board.GP7, board.GP8,                # 9 (rec), 10 (play), 11 (stop), 
    board.GP9, board.GP10, board.GP19, board.GP20   # 12 (up/dn), 13 (A), 14 (B), 15 (shift)
)
num_leds = len(led_pins)

# oops getting "RuntimeError: Internal resource(s) in use"
# when trying to PWM all the LED pins
# so will just on/off them for now

# map LEDs to as close an a clockwise radial circle as possible
demo_led_map = (0,1,2,3, 11,12,13,14, 7,10,6,9,5,8,4)  # circle around clockwise

# map touch pad index to LED
# (some multiple pads map to a single LED, some touch inputs are not wired)
pad_to_led = (
    4, 5, 6, 7,     # 1,2,3,4
    0, 1, 2, 3,     # 5,6,7,8
    8, 9 ,10,       # rec, play, stop
    11, 11, 11,     # up, center, down
    12, 13, 14,     # A, B, shift
    None, None, None,     # not wired
)
# fmt: on

midi_base = 42
pad_to_midi = ( 0, 2, 4, 5, 7, 9, 10, 12)

class DrumCardHardware:
    def __init__(self):
        i2c = busio.I2C(scl=i2c_scl_pin, sda=i2c_sda_pin, frequency=1_000_000)
        self.ts20 = ts20.TS20(i2c)

        self.uart = busio.UART(tx=midi_out_pin, rx=midi_in_pin, baudrate=31250, timeout=0.0001)
        self.midi_usb = tmidi.MIDI(midi_in=usb_midi.ports[0], midi_out=usb_midi.ports[1])
        self.midi_uart = tmidi.MIDI(midi_in=self.uart)

        # set up the synth->audio system
        self.audio = audiopwmio.PWMAudioOut(audio_pin)
        self.mixer = audiomixer.Mixer(voice_count=1, sample_rate=22050, channel_count=1,
                                      bits_per_sample=16, samples_signed=True,
                                      buffer_size=2048)  # need a big buffer when screen updated
        self.synth = synthio.Synthesizer(sample_rate=22050)
        self.audio.play(self.mixer)
        self.mixer.voice[0].level = 0.75 # turn down the volume a bit since this can get loud
        self.mixer.voice[0].play(self.synth)
        # set up the synth
        self.wave_saw = np.linspace(30000,-30000, num=256, dtype=np.int16)  # default squ is too clippy
        amp_env = synthio.Envelope(sustain_level=0.8, release_time=0.1, attack_time=0.001)
        self.synth.envelope = amp_env

        self.leds = []

        for pin in led_pins:
            print("pin:", pin)
            led = digitalio.DigitalInOut(pin)
            led.switch_to_output(value=False)
            self.leds.append(led)

    def set_led(self, n, val):
        self.leds[n].value = val
        
    def set_leds(self, val):
        for l in self.leds: l.value = val

    def read_touch(self):
        self.touches = self.ts20.read_touches()
        return self.touches

    def update(self):
        self.read_touches()

    def startup_demo(self):
        print("picotouch_drumcard_hwtest: startup demo")

        for j in range(2):
            for i in range(num_leds):
                self.set_led(demo_led_map[i], True)
                f = synthio.midi_to_hz(random.randint(32,72))
                note = synthio.Note(frequency=f)
                hw.synth.press(note)
                time.sleep(0.03)
                self.set_led(demo_led_map[i], False)
                hw.synth.release(note)
                time.sleep(0.03)

    def bad_touch(self):
        return False
        #return self.touches.count(1) > 2
        # return ((touches[7] and touches[8] and touches[9]) or
        #         (touches[9] and touches[10] and touches[11]) or
        #         (touches[10] and touches[11] and touches[12]))

        
def midi_handler(hw):
    while msg := hw.midi_uart.receive() or hw.midi_usb.receive():
        if msg.type == tmidi.NOTE_ON:
            chan = msg.channel
            note = msg.data0
            vel = msg.data1
            print('NoteOn: Ch: {} Note: {} Vel:{}'.format(chan, note, vel))
            hw.synth.press( note )
        elif msg.type == tmidi.NOTE_OFF:
            chan = msg.channel
            note = msg.data0
            vel = msg.data1
            print('NoteOff: Ch: {} Note: {} Vel:{}'.format(chan, note, vel))
            hw.synth.release( note )
        elif msg.type == tmidi.PITCH_BEND:
            chan = msg.channel
            pbval = (msg.data1 << 7) | msg.data0
            print("PitchBend: Ch: {} Bend: {}".format(chan, pbval))
        elif msg.type == tmidi.CC:
            chan = msg.channel
            ccnum = msg.data0
            ccval = msg.data1
            print('CC Ch: {}, Num: {} Val: {}'.format(chan, ccnum, ccval))
        elif msg.type == tmidi.CHANNEL_PRESSURE:
            chan = msg.channel
            press_val = msg.data0
            print('Ch Pressure: Ch: {}, Val: {}'.format(chan, press_val))
        elif msg.type == tmidi.SYSTEM_RESET:
            print('System reset')
        else:
            print("unknown message:",msg)

hw = DrumCardHardware()
hw.startup_demo()

print("picotouch_drumcard_hwtest: ready")
last_time = 0
last_led_time = 0

last_touches = hw.read_touch()

notes = [None] * 8

while True:
    midi_handler(hw)

    touches = hw.read_touch()

    for i, t in enumerate(touches):
        if t and not last_touches[i]:  # pressed
            ledi = pad_to_led[i]
            hw.set_led(ledi, t)
            if i < 8:
                notes[i] = synthio.Note(synthio.midi_to_hz(midi_base + pad_to_midi[i])) # waveform=hw.wave_saw)
                hw.synth.press(notes[i])
        if not t and last_touches[i]: # released
            ledi = pad_to_led[i]
            hw.set_led(ledi, t)
            if i < 8:
                hw.synth.release(notes[i])
            
    last_touches = touches
    
    
    now = time.monotonic()
    if now - last_led_time > 0.3:
        last_led_time = now
        #hw.set_leds(False)
        
    if now - last_time > 0.1:
        last_time = now
        #touches = hw.read_touch()
        print("%.2f" % time.monotonic(), touches)
            
                


# for pin in led_pins:
#     print("pin:",pin)
#     led = pwmio.PWMOut(pin, frequency=25000, duty_cycle=0)
#     leds.append(led)
    
# def set_led(n, val=1.0):
#     leds[n].duty_cycle = int(65535 * val)
    
# def dim_all_leds(amount=0.95):
#     """Dim all LEDs by an amount"""
#     for led in leds:
#         led.duty_cycle = int(led.duty_cycle * amount)

# demo_led_map = (0,1,2,3, 8,9,10, 7,6,5,4)  # circle around clockwise
# for j in range(5):
#     for i in range(num_leds):
#         set_led(demo_led_map[i], 1)
#         dim_all_leds(0.7)
#         time.sleep(0.05)

