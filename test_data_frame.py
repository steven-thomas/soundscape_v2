"""
Steven Thomas (2020-09)
TODO: add licence/copyright note
"""

import numpy as np
import time

from data_frame import DataController
from audio import AudioController

N = 5
arr1 = 2*np.arange(N)
arr2 = 2+np.arange(N)
stip1 = (np.arange(N) % 2)
stip2 = None
label = None

audio = AudioController()
func = audio.update

data = DataController( arr1, arr2, stip1, stip2, label, func )

audio.start_stream()
print( 'at start: {:}'.format(data.get_label()) )
for x in range(N):
    data.update( x, 0 )
    print( data.get_label() )
    time.sleep(1.0)
print( 'end test' )
audio.end_stream()
