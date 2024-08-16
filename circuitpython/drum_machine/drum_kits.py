
#
# Drum kit management
#
import os
import audiocore

def find_kits(kit_root="/drumkits", num_pads=8):
    """
    Search a given drum kit directory for subdirs containing drum kits
    Then load up the drum kit info into "kits" data struct:
    keys = kit names, values = list of WAV sample filenames
    also special key "kit_names" as ordered list of kit names.

    Kit directories should be named like:
      00kick, 01snare, 02hatC, 03hatO, 04clap, 05tomL, 06ride, 07crash,
    if there aren't 8 smamples, it will not add the kit
    """
    kits = {}
    for kitname in sorted(os.listdir(kit_root)):
        kname = kitname.lower()
        if not kname.startswith("kit"): # ignore non-kit dirs
            continue
        kits[kname] = []  # holds all sample names of given kit
        for samplename in sorted(os.listdir(f"{kit_root}/{kname}")):
            samplename = samplename.lower()
            if samplename.endswith(".wav") and not samplename.startswith("."):
                kits[kname].append(f"{kit_root}/{kname}/{samplename}") # add it to the bag!
        if len(kits[kname]) < num_pads:
            print(f"ERROR: kit '{kname}' not enough samples! Removing...")
            del kits[kname]
    kits['kit_names'] = sorted(kits.keys())  # add special key of sorted names
    return kits


def load_drumkit(kits, kit_index):
    """
    Load WaveFile objects upfront into waves array, by kit index,
    in attempt to reduce play latency
    """
    kit_name = kits['kit_names'][kit_index]
    num_pads = len(kits[kit_name])
    waves = [None] * num_pads
    for i in range(num_pads):
        fname = kits[kit_name][i]
        waves[i] = audiocore.WaveFile(fname)
    return waves, num_pads

# # play a drum sample, either by sequencer or pressing pads
# def play_drum(num, pressed):
#     pads_lit[num] = pressed
#     voice = mixer.voice[num]   # get mixer voice
#     if pressed and not pads_mute[num]:
#         voice.play(waves[num],loop=False)
#     else: # released
#         pass   # not doing this for samples
