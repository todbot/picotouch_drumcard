import time
import random
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
    board.GP6, board.GP7, board.GP8,                # 9 (stop), 10 (play), 11 (rec)
    board.GP9, board.GP10, board.GP19, board.GP20   # 12 (up/dn), 13 (A), 14 (B), 15 (shift)
)
num_leds = len(led_pins)

# oops getting "RuntimeError: Internal resource(s) in use"
# when trying to PWM all the LED pins
# so will just on/off them for now

# map LEDs to as close an a clockwise radial circle as possible
demo_led_map = (0,1,2,3, 11,12,13,14, 7,10,6,9,5,8,4)  # circle around clockwise

# # map idealized LED number to physical LED pin number
# led_map = ( 4, 5, 6, 7,  # pads 1-4
#             0, 1, 2, 3,  # pads 5-8
#             8, 9, 10,    # pads stop, play, rec
#            )
            
# map touch pad index to LED
# (some multiple pads map to a single LED, some touch inputs are not wired)
pad_to_led = (
    0, 1, 2, 3,     # 5,6,7,8
    4, 5, 6, 7,     # 1,2,3,4
    8, 9 ,10,       # stop, play, rec
    11, 11, 11,     # up, center, down
    12, 13, 14,     # A, B, shift
    None, None, None,     # not wired
)
# fmt: on


class DrumCardHardware:

    LED_STOP = 8
    LED_PLAY = 9
    LED_REC = 10

    # symbolic names for padids
    PAD_1 = 0
    PAD_2 = 1
    PAD_3 = 2
    PAD_4 = 3
    PAD_5 = 4
    PAD_6 = 5
    PAD_7 = 6
    PAD_8 = 7
    PAD_STOP = 8    
    PAD_PLAY = 9
    PAD_REC = 10
    PAD_UP = 11
    PAD_MID = 12
    PAD_DOWN = 13
    PAD_A = 14
    PAD_B = 15
    PAD_SHIFT = 16

    def __init__(self, sample_rate=22050, num_voices=8):
        self.sample_rate = sample_rate
        self.num_voices = num_voices
        i2c = busio.I2C(scl=i2c_scl_pin, sda=i2c_sda_pin, frequency=400_000)
        self.ts20 = ts20.TS20(i2c)

        self.uart = busio.UART(tx=midi_out_pin, rx=midi_in_pin, baudrate=31250, timeout=0.0001)
        self.midi_usb = tmidi.MIDI(midi_in=usb_midi.ports[0], midi_out=usb_midi.ports[1])
        self.midi_uart = tmidi.MIDI(midi_in=self.uart)

        # set up the synth->audio system
        self.audio = audiopwmio.PWMAudioOut(audio_pin)
        self.mixer = audiomixer.Mixer(voice_count=num_voices, sample_rate=sample_rate,
                                      channel_count=1, bits_per_sample=16, samples_signed=True,
                                      buffer_size=2048) 
        self.leds = []
        for pin in led_pins:
            print("pin:", pin)
            led = digitalio.DigitalInOut(pin)
            led.switch_to_output(value=False)
            self.leds.append(led)

    def start_synth(self, level=0.75):
        self.synth = synthio.Synthesizer(sample_rate=self.sample_rate)
        self.audio.play(self.mixer)
        self.mixer.voice[0].level = level # turn down the volume a bit since this can get loud
        self.mixer.voice[0].play(self.synth)
        
        # set up the synth
        self.wave_saw = np.linspace(30000,-30000, num=256, dtype=np.int16)  # default squ is too clippy
        amp_env = synthio.Envelope(sustain_level=0.8, release_time=0.1, attack_time=0.001)
        self.synth.envelope = amp_env
        
    def start_sampleplayer(self):
        pass

    def set_led(self, n, val):
        self.leds[n].value = val

    def set_led2(self, n, val):
        """
        Set an LED according to  padid number:
        0-7 : pads 1-8
        9 : 
        """
        self.leds[pad_to_led[n]].value =  val
        
    def set_leds(self, val):
        for l in self.leds: l.value = val

    def pad_to_led(self, i):
        return pad_to_led[i]

    def read_touch(self):
        touches = self.ts20.read_touches()
        # swizzle first four and second four to match layout weirdness I did
        touches[0:4], touches[4:8] = touches[4:8],touches[0:4]
        self.touches = touches
        return self.touches

    def update(self):
        self.read_touches()

    def startup_demo(self, n=2, t=0.02):
        print("picotouch_drumcard: startup demo")

        for j in range(n):
            for i in range(num_leds):
                self.set_led(demo_led_map[i], True)
                f = synthio.midi_to_hz(random.randint(32,72))
                note = synthio.Note(frequency=f)
                self.synth.press(note)
                time.sleep(t)
                self.set_led(demo_led_map[i], False)
                self.synth.release(note)
                time.sleep(t)

    def bad_touch(self):
        ts = self.touches
        return (
            #(ts.count(1) > 2) or
            (ts[20]) or
            ((ts[7] and ts[8] and t[9]) or
             (ts[9] and ts[10] and ts[11]) or
             (ts[10] and ts[11] and ts[12]))
        )
