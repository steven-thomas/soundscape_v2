"""
Try to play a sample tone on every device that claims to support required output.
"""
import numpy as np
import time
import pyaudio

#sample_rate 44100 == CD quality
sample_rate = 44100
#max size of 16-bit signed integer
int16_max = 32767
#sampwidth 2 == unsigned 16-bit integer
sampwidth = 2

channels = 2
volume = 1.0
tlen = 1.0 #seconds
freq = 440.

def make_swave( freq ):
    nsample = int( sample_rate * tlen )
    arr = np.arange(nsample).astype(float)
    sinewave = np.sin(2*np.pi*freq*(arr/float(sample_rate)))
    soundwave = (volume * int16_max * sinewave).astype( np.int16 )
    return soundwave

swave = make_swave( freq )
offset = 0

def callback(in_data, frame_count, time_info, status):
    global offset
    index = int(frame_count+offset)
    pair = np.zeros(2*frame_count).astype(np.int16)
    pair[::2] = swave[offset:index]
    pair[1::2] = swave[offset:index]
    data = pair.tobytes()
    offset = int( index % (sample_rate/freq) )
    return (data, pyaudio.paContinue)



p = pyaudio.PyAudio()

#info = p.get_default_output_device_info()
#for key, value in info.items():
#    print( '{:} - {:}'.format(key,value) )

api_info =  p.get_default_host_api_info()
print( 'default Host API parameters:' )
for key,value in api_info.items():
    print( ' - {:} = {:}'.format(key,value) )

ndev = p.get_device_count()
print( 'No. of devices = {:}'.format(ndev) )
audio_format = p.get_format_from_width( sampwidth )

for i in range(ndev):
    print('\n')
    use_device = False
    try:
        p.is_format_supported( rate=sample_rate,
                               output_device=i,
                               output_channels=channels,
                               output_format=audio_format )
        use_device = True
    except Exception as e:
        print( e )

    if use_device:# and i not in [<list of dud devices>]:
        print( 'Output Device Index - {:}'.format(i) )
        dev_info = p.get_device_info_by_index(i)
        print( 'name = {:}'.format(dev_info['name']) )
        #for key,value in dev_info.items():
        #    print( '{:} - {:}'.format(key,value) )
        stream = p.open( format=audio_format,
                         channels=channels,
                         rate=sample_rate,
                         output=True,
                         stream_callback=callback,
                         output_device_index=i )
        stream.start_stream()
        time.sleep(1.0)
        stream.stop_stream()
        stream.close()

# close PyAudio (7)
p.terminate()
