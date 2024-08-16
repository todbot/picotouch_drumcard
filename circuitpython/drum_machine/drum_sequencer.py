
from adafruit_ticks import ticks_ms, ticks_diff, ticks_add
import drum_patterns


debug = True

# stub function so you can opt to not pass in a trig_on or trig_off function
def trigstub(padid, pos):  pass

class DrumSequencer():
    """
    """
    def __init__(self, bpm, patterns, trig_on=None, trig_off=None):
        self.last_step_millis = ticks_ms()
        self.playing = False
        self.recording = False
        self.steps_per_beat = 8  # divisions per beat: 8 = 32nd notes, 4 = 16th notes
        self.patterns = patterns
        self.num_patterns = len(patterns)
        self.pos = 0  # where in our sequence we are
        self.trig_on = trig_on if trig_on is not None else trigstub
        self.trig_off = trig_off if trig_off is not None else trigstub
        self.set_bpm(bpm)
        
        # first pattern determines number of steps & pads in all sequences
        self.change_pattern(0)
        self.num_steps = len(self.sequence)
        self.num_pads = len(self.sequence[0])
        self.triggered = [False] * self.num_pads  # which pads are triggered       
        
    def change_pattern(self,patt_index):
        self.patt_index = patt_index % self.num_patterns
        self.sequence = self.patterns[self.patt_index]['seq']

    def set_trig(self, trigid, val= True, pos=None):
        if pos is None:
            pos = self.pos
        if self.playing:
            pos = pos-1  # it's always in the future when playing
        self.sequence[pos][trigid] = val
        
    # def toggle_trig(self, trigid, pos=None):
    #     if pos is None:
    #         pos = self.pos
    #     if self.playing:
    #         pos = pos-1  # it's always in the future when playing
    #     self.sequence[pos][trigid] = not self.sequence[pos][trigid]

    def clear_trigs(self, trigid):
        for i in range(self.num_steps):
            self.sequence[i][trigid] = 0

    def set_bpm(self, bpm):
        """
        Set BPM. Beat timing assumes 4/4 time signature,
        e.g. 4 beats per measure, 1/4 note gets the beat
        """
        beat_time = 60 / bpm  # time length of a single beat
        beat_millis = beat_time * 1000  # time length of single beat in millis
        # time length of a beat subdivision, e.g. 1/16th note
        self.step_millis = int(beat_millis / self.steps_per_beat)
        # and keep "step_millis" an int so diff math is fast
        # FIXME: what about int round-down problem?

    def update(self):
        now = ticks_ms()
        diff = ticks_diff( now, self.last_step_millis )
        if diff < self.step_millis:
            if diff > 2:
                # untrigger any triggered pads
                for i in range(self.num_pads):
                    if self.triggered[i]:
                        self.trig_off(i, self.pos)
                        self.triggered[i] = False
            return
        self.last_step_millis = now

        late_millis = ticks_diff( diff, self.step_millis )  # how much are we late
        self.last_step_millis = ticks_add( now, -(late_millis//2) ) # attempt to make it up on next step

        # play any sounds recorded for this step
        if self.playing:
            
            # fixme: also turn off any
            step_line = self.sequence[self.pos]
            #self.step_cb( self.pos, step_line)
            
            # go through any pads, seeing which notes to trigger
            for i in range(self.num_pads):
                # play_drum(i, sequence[i][pos] ) # FIXME: what about note-off
                if step_line[i]:
                    self.trig_on(i, self.pos)
                    self.triggered[i] = True

        self.pos = (self.pos + 1) % self.num_steps

    def at_step(self):
        # tempo indicator (leds.show() called by LED handler)
        return self.pos % self.steps_per_beat == 0
        #if pos % steps_per_beat == 0:    leds[key_TAP_TEMPO] = 0x333333
        #if pos == 0:   leds[key_TAP_TEMPO] = 0x3333FF # first beat indicator

    @classmethod
    def load_patterns(cls, filepath):
        return load_patterns(filepath)


#------------------------------------------------------------------------

""""
pattern sequence data structure
-------------------------------
On disk (as either JSON or .py), a sequence looks like
a list of instruments, containing list of steps as strings, e.g.:

patterns = [
  { 'name': 'patt0',
    'seq': [
            #steps       11 1111  1111 2222 2222 2233
            #0123 4567 8901 2345  6789 0123 4567 8901
            '1000 0000 1000 1000  1000 0000 1000 0000', # bd
            '0000 1000 1000 1000  0000 1000 0000 1000', # sd
            '1010 1010 1010 1010  1010 1010 1010 1000', # oh
            '0000 0000 0000 0000  0000 0000 0000 0010', # ch
            ... and so on to num_pads (8)
            ]
 },
]

In memory, the sequence is transposed and expanded to
a list of time steps, each containing a list of triggers, e.g.:

patterns = [
 { 'name': 'patt0',
    'seq': [
      # bd sd oh ch
      [ 1, 0, 0, 0,  0,0,0,0 ], # time step 0
      [ 0, 0, 0, 0,  0,0,0,0 ], # time step 1
      [ 0, 0, 1, 0,  0,0,0,0 ], # time step 2
      [ 0, 0, 0, 0,  0,0,0,0 ], # time step 3
      ... and so on up to 'len'
  },
]

"""

def load_patterns(cls, filepath="/saved_patterns.json", load_demo=True):
    patts = []
    try:
        with open(filepath,'r') as fp:
            patts = json.load(fp)
            for p in patts:
                # convert str of '1010' to array 1,0,1,0, eliding whitespace, for all seq lines
                p['seq'] = [int(c) for c in s.replace(' ','') for s in p['seq']]
    except (OSError, ValueError) as error:  # maybe no file
        print("load_patterns:",error)

    if len(patts) == 0: # no patterns
        if load_demo: # load demo instead
            print("no saved patterns, loading demo patterns")
            pypatts = drum_patterns.patterns_demo
        else:
            pypatts = drum_patterns.patterns_blank
            print("no saved patterns, loading blank pattern")
        patts = []
        for p in drum_patterns.patterns_demo:
            patts.append( {'name':p['name'], 'seq': make_sequence_from_pypattern(p) } )
        return patts


def make_sequence_from_pypattern(patt):
    """
    Turn a python pattern (e.g. stored in "drum_patterns.py") to an internal sequence list
    """
    # get length of pattern and num pads from pattern string rep
    num_steps = len(patt['seq'][0].replace(' ',''))
    num_pads = len(patt['seq'])
    seq = []
    # first convert '1010...' step strings to 1,0,1,0 numeric array
    for stepline_str in patt['seq']:
        stepline = [int(c) for c in stepline_str.replace(' ','')]
        seq.append(stepline)

    # now transpose the matrix to make it a list of trigs in a list of steps
    seqt = []
    for i in range(num_steps):
        seqt.append( [seq[j][i] for j in range(num_pads)] )
    return seqt


####################################

last_write_time = 0 #time.monotonic()
def save_patterns(patterns):
    global last_write_time
    print("saving patterns...", end='')
    #if ticks_ms() - last_write_time < 10: # only allow writes every 10 seconds, to save flash
    #    print("NO WRITE: TOO SOON")
    #    return
    #last_write_time = time.monotonic()
    patts_to_sav = []
    for p in patterns:
        seq_to_sav = [''.join(str(c) for c in l) for l in p['seq']]
        patts_to_sav.append( {'name': p['name'], 'seq': seq_to_sav } )
    with open('/test_saved_patterns.json', 'w') as fp:
    #with sys.stdout as fp:
        json.dump(patts_to_sav, fp)
    print("\ndone")


def copy_pattern(patt_index):
    pass

def copy_current_pattern():
    global patt_index, sequence
    pname = patterns[patt_index]['name']
    #seq_new = [l.copy() for l in patterns[patt_index]['seq']]  # copy list of lists
    seq_new = [l.copy() for l in sequence]  # copy list of lists
    new_patt = { 'name': 'cptst1',
                 'seq': seq_new }
    patt_index = patt_index + 1
    patterns.insert(patt_index, new_patt)
    sequence = patterns[patt_index]['seq']
