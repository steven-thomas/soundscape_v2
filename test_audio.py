"""
Steven Thomas (2020-09)
TODO: add licence/copyright note
"""

from audio import SoundController
import config as cfg

audio = SoundController()

help_msg = """enter a pair of numbers between 0 and {0:}, seperated by a space.
0 = mute channel, 1-{0:} = frequencies between {1:}Hz and {2:}Hz.
add 's' to the end of a channel to stipple it.
type 'end' to end the test.""".format(cfg.nfreq, cfg.min_freq, cfg.max_freq)

print( help_msg )
audio.start_stream()
audio.update( [0,False,False], [0,False,False] )

while True:
    raw_in = input('sound-test:')
    raw_in = raw_in.strip().lower()
    if raw_in == 'end':
        break
    elif raw_in == '' or raw_in == 'help':
        print( help_msg )
    else:
        def parse_in( in_str ):
            if in_str[0] == '0':
                #mute channel
                return [ 0, False, True ]
            elif in_str[-1] == 's':
                signal = [ None, True, False ]
                val = int( in_str[:-1] )
            else:
                signal = [ None, False, False ]
                val = int( in_str )
            if 1 <= val <= cfg.nfreq:
                signal[0] = val-1
                return signal
            else:
                print( 'invalid channel input.' )
                return [ 0, False, True ]
        in_pair = raw_in.strip().lower().split()
        if len(in_pair) == 2:
            sig1 = parse_in( in_pair[0] )
            sig2 = parse_in( in_pair[1] )
            print( '{:} / {:}'.format(sig1,sig2) )
            audio.update( sig1, sig2 )
        else:
            print( 'invalid entry.' )
audio.end_stream()
print( 'end test.' )
