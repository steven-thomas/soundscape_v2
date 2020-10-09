"""
Steven Thomas (2020-09)
TODO: add licence/copyright note
"""

#zoom level per keypress, 0=no zoom, 1=double spacing
zoom_lvl = 0.5
#pad to cut off each side of screen (fraction of screen)
x_pad = 0.02
y_pad = 0.02

#volume for array tones, 0=mute, 1=max volume
volume = 0.8
#volume boost for stipple sounds ( boost + volume <= 1. )
stipple_boost = 0.1
#number of frequencies in sound map
nfreq = 25
#lowest frequency to use (Hz)
min_freq = 350
#highest frequency to use (Hz)
max_freq = 1400
#frequency of stipple effect (Hz)
stipple_freq = 10
#audio sample rate, 44100=CD/DVD quality
samp_rate = 44100
#length of generated sound samples (seconds)
samp_len = 0.5
#output audio device index (None = use default)
device_index = None
