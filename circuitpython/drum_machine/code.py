# import time, board, busio

# from ts20 import TS20

# i2c_sda_pin = board.GP16
# i2c_scl_pin = board.GP17

# i2c = busio.I2C(i2c_scl_pin, i2c_sda_pin)

# ts20 = TS20(i2c)

# print("hi")

# while True:
#     touches = ts20.read_touches()
#     print(touches)
#     time.sleep(0.02)

    


##############################################################


# SPDX-FileCopyrightText: Copyright (c) 2024 Tod Kurt
# SPDX-License-Identifier: MIT
"""
picotouch_drumcard_drum_machine.py --
31 Jul 2024 - @todbot / Tod Kurt
Part of https://github.com/todbot/picotouch_drumcard
"""

import asyncio
import gc
import time
import random
import synthio
import tmidi

from adafruit_ticks import ticks_ms, ticks_diff, ticks_add

from drumcard_hardware import DrumCardHardware

from drum_kits import find_kits, load_drumkit
from drum_sequencer import DrumSequencer


midi_base = 42
pad_to_midi = ( 0, 2, 4, 5, 7, 9, 10, 12)
        
kits = find_kits()
kit_index = 0
waves, num_trigs = load_drumkit(kits, kit_index)
print("kits:",kits, "\nnum_trigs:", num_trigs)

hw = DrumCardHardware()
hw.start_synth()
#hw.startup_demo()
hw.start_sampleplayer()

pad_lit_millis = 100
pads_lit = [False] * num_trigs

# callback function called by sequencer
def drum_on(trigid, seqpos=None):
    #print("drum_on:",trigid, seqpos)
    voice = hw.mixer.voice[trigid]   # get mixer voice
    voice.play(waves[trigid], loop=False)
    hw.set_led(trigid, True)
    pads_lit[trigid] = True
    #gc.collect()

# callback function called by sequencer
def drum_off(trigid, seqpos=None):
    #print("drum_off:", trigid)
    pass

patterns = DrumSequencer.load_patterns("/saved_patterns.json")
seq = DrumSequencer(120, patterns, trig_on=drum_on, trig_off=drum_off)

seq.change_pattern(1)
seq.playing = True

last_padlit_millis = ticks_ms()
last_debug_millis = ticks_ms()
rec_mode = False
rec_held = False

touches = []

# # play a drum sample, either by sequencer or pressing pads
# def play_drum(num, on=True):
#     voice = hw.mixer.voice[num]   # get mixer voice
#     if on:
#         voice.play(waves[num], loop=False)
#         pass
#     else:
#         voice.stop()

async def seq_updater():
    while True:
        seq.update()
        await asyncio.sleep(0.001)
        
async def midi_handler():
    while True:
        await asyncio.sleep(0.001)
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

async def ui_handler():
    global rec_mode, rec_held, touches
    trig_pressed = False
    last_padlit_millis = ticks_ms()
    last_touches = hw.read_touch()
    
    while True:
        await asyncio.sleep(0.05)
        # update playstate
        hw.set_led(hw.LED_PLAY, seq.playing)
        hw.set_led(hw.LED_REC, rec_mode or rec_held)

        touches = hw.read_touch()
        #if hw.bad_touch(): continue
        
        # read touchpad
        for i, t in enumerate(touches):
            if i > 15: continue  # not wired inputs
            if t and not last_touches[i]:  # pressed
                ledi = hw.pad_to_led(i)
                hw.set_led(ledi, t)
                if i < 8:  # is drumpad, not control
                    trig_pressed = True
                    if rec_mode:
                        seq.set_trig(i)
                        drum_on(i)
                    else:
                        drum_on(i)  # normal playing
                elif i == hw.PAD_PLAY:
                    seq.playing = not seq.playing
                elif i == hw.PAD_STOP:
                    seq.playing = False
                    seq.pos = 0
                elif i == hw.PAD_REC:
                    rec_held = True
                elif i == hw.PAD_A:
                    seq.change_pattern(seq.patt_index+1)
                elif i == hw.PAD_B:
                    seq.change_pattern(seq.patt_index-1)
            
            if not t and last_touches[i]: # released
                ledi = hw.pad_to_led(i)
                hw.set_led(ledi, t)
                if i< 8:
                    if rec_held:
                        seq.clear_trigs(i)
                        
                elif i == hw.PAD_REC:
                    rec_held = False
                    if trig_pressed:
                        trig_pressed = False
                    else:
                        rec_mode = not rec_mode
                
        last_touches = touches

        now_millis = ticks_ms()
        # turn off any triggered pads after a while
        if ticks_diff(now_millis, last_padlit_millis) > pad_lit_millis:
            last_padlit_millis = now_millis
            for i in range(num_trigs):
                if pads_lit[i]:
                    pads_lit[i] = False
                    hw.set_led(i, False)

        
async def debug_handler():
    while True:
        print("debug: ", touches)
        await asyncio.sleep(1)
        
    #     #print("%.2f %.2f" % (time.monotonic(), dt), touches)
        

    # # debugging touch output
    # if ticks_diff(now_millis, last_debug_millis) > 100:
    #     last_debug_millis = now_millis
    #     #print("%.2f %.2f" % (time.monotonic(), dt), touches)
    #     print("%.2f %.2f" % (time.monotonic(), dt))

print("picotouch_drumcard_drum_machine: ready")

async def main():
    task2 = asyncio.create_task(ui_handler())
    task3 = asyncio.create_task(midi_handler())
    task4 = asyncio.create_task(seq_updater())
    task5 = asyncio.create_task(debug_handler())
    await asyncio.gather(task2, task3, task4, task5)

asyncio.run(main())

# #gc.disable()

# while True:
#     dt = time.monotonic()
#     midi_handler()
#     seq.update()
    
#     # update playstate
#     hw.set_led(hw.LED_PLAY, seq.playing)
#     hw.set_led(hw.LED_REC, rec_mode or rec_held)

#     touches = hw.read_touch()
#     if hw.bad_touch(): continue

#     # read touchpad
#     for i, t in enumerate(touches):
#         if i > 15: continue  # not wired inputs
#         if t and not last_touches[i]:  # pressed
#             ledi = hw.pad_to_led(i)
#             hw.set_led(ledi, t)
#             if i < 8:  # is drumpad, not control
#                 if rec_held:
#                     seq.clear_trigs(i)
#                 elif rec_mode:
#                     seq.set_trig(i)
#                     play_drum(i)
#                 else:
#                     play_drum(i)  # normal playing
#             elif i == hw.PAD_PLAY:
#                 seq.playing = not seq.playing
#             elif i == hw.PAD_STOP:
#                 seq.playing = False
#                 seq.pos = 0
#             elif i == hw.PAD_REC:
#                 rec_held = True
#             elif i == hw.PAD_A:
#                 seq.change_pattern(seq.patt_index+1)
#             elif i == hw.PAD_B:
#                 seq.change_pattern(seq.patt_index-1)
            
#         if not t and last_touches[i]: # released
#             ledi = hw.pad_to_led(i)
#             hw.set_led(ledi, t)
#             if i< 8:
#                 pass
#                 #play_drum(i,False)
#             elif i == hw.PAD_REC:
#                 rec_held = False
#                 rec_mode = not rec_mode
                
#     last_touches = touches

#     dt = (time.monotonic() - dt) * 1000
        
#     now_millis = ticks_ms()
    
#     # turn off any triggered pads after a while
#     if ticks_diff(now_millis, last_padlit_millis) > pad_lit_millis:
#         last_padlit_millis = now_millis
#         for i in range(num_trigs):
#             if pads_lit[i]:
#                 pads_lit[i] = False
#                 hw.set_led(i, False)

#     # debugging touch output
#     if ticks_diff(now_millis, last_debug_millis) > 100:
#         last_debug_millis = now_millis
#         #print("%.2f %.2f" % (time.monotonic(), dt), touches)
#         print("%.2f %.2f" % (time.monotonic(), dt))
           



    
    # for i, t in enumerate(touches):
    #     if i > 15: continue  # not wired inputs
    #     if t and not last_touches[i]:  # pressed
    #         ledi = hw.pad_to_led(i)
    #         hw.set_led(ledi, t)
    #         if i < 8:
    #             notes[i] = synthio.Note(synthio.midi_to_hz(midi_base + pad_to_midi[i])) # waveform=hw.wave_saw)
    #             hw.synth.press(notes[i])
    #     if not t and last_touches[i]: # released
    #         ledi = hw.pad_to_led(i)
    #         hw.set_led(ledi, t)
    #         if i < 8:
    #             hw.synth.release(notes[i])
        
