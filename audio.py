"""
Steven Thomas (2020-09)
TODO: add licence/copyright note
"""

import numpy as np
import pyaudio

import config as cfg

class Channel( object ):
    "Handles channel data"
    def __init__(self):
        self.update( silent=True )
        return None
    
    def get(self, frame_count):
        "Get array of frame data"
        if self.silent:
            out_wave = np.zeros( frame_count ).astype( np.int16 )
        else:
            #get indexes for wave slice
            first_ind = self.offset
            last_ind = int( frame_count + self.offset )
            #get slice of waveform
            out_wave = self.wave[ first_ind:last_ind ]
            #update offset to remove discontinuity 'click'
            #self.offset = int( last_ind % (cfg.samp_rate/self.freq) )
            rollover = cfg.samp_rate * float(cfg.stipple_freq) / float(self.freq)
            self.offset = int( last_ind % rollover )
        return out_wave
        
    def update(self, freq=None, wave=None, silent=None):
        "change sound playing through channel"
        if silent:
            self.offset = 0
            self.freq = 0
            self.wave = None
            self.silent = True
        else:
            self.offset = int( self.freq*self.offset / freq )
            self.freq = freq
            self.wave = wave
            self.silent = False
        return None



class SoundController( object ):
    """Main controller for sound."""
    def __init__(self):
        self.ch_1 = Channel()
        self.ch_2 = Channel()
        #status = [freq_index, stipple_flag, silent_flag] for each channel
        self.status_1 = [ 0, False, True ]
        self.status_2 = [ 0, False, True ]
        self.freq_list = list( np.logspace( np.log2(cfg.min_freq),
                                            np.log2(cfg.max_freq),
                                            num=cfg.nfreq,
                                            endpoint=True, base=2.0 ) )
        self.tone_wave_list = [ self.make_wave(f,False) for f in self.freq_list ]
        self.stipple_wave_list = [ self.make_wave(f,True) for f in self.freq_list ]
        return None

    def make_wave( self, freq, stipple=False ):
        #max size of 16-bit signed integer
        int16_max = 32767
        stipple_freq = 10.

        nsample = int( cfg.samp_rate * cfg.samp_len )
        arr = np.arange(nsample).astype(float)
        sinewave = np.sin(2*np.pi*freq*(arr/float(cfg.samp_rate)))
        if stipple:
            stipple_wave = np.sin(2*np.pi*(cfg.stipple_freq)*(arr/float(cfg.samp_rate)))
            sinewave *= stipple_wave
        soundwave = (cfg.volume * int16_max * sinewave).astype( np.int16 )
        return soundwave

    def update( self, s_1, s_2 ):
        """update channel sounds if changed."""
        #signal = [freq_index, stipple_flag, silent_flag] for each channel
        signal_1 = [ int(s_1[0]), bool(s_1[1]), bool(s_1[2]) ]
        signal_2 = [ int(s_2[0]), bool(s_2[1]), bool(s_2[2]) ]
        if signal_1 != self.status_1:
            index, is_stipple, is_silent = signal_1
            if is_silent:
                self.ch_1.update( silent=True )
            else:
                freq = self.freq_list[index]
                if is_stipple:
                    wave = self.stipple_wave_list[index]
                else:
                    wave = self.tone_wave_list[index]
                self.ch_1.update( freq=freq, wave=wave, silent=False )
            self.status_1 = [ i for i in signal_1 ]
        if signal_2 != self.status_2:
            index, is_stipple, is_silent = signal_2
            if is_silent:
                self.ch_2.update( silent=True )
            else:
                freq = self.freq_list[index]
                if is_stipple:
                    wave = self.stipple_wave_list[index]
                else:
                    wave = self.tone_wave_list[index]
                self.ch_2.update( freq=freq, wave=wave, silent=False )
            self.status_2 = [ i for i in signal_2 ]
        return None
    
    def _callback( self, in_data, frame_count, time_info, status ):
        """callback function for pyAudio stream."""
        out_arr = np.zeros(2*frame_count).astype(np.int16)
        #interleave 2 channels into output
        out_arr[::2] = self.ch_1.get( frame_count )
        out_arr[1::2] = self.ch_2.get( frame_count )
        data = out_arr.tobytes()
        return ( data, pyaudio.paContinue )

    def start_stream(self):
        """turn on pyAudio stream"""
        sampwidth = 2 #16-bit unsigned.
        nchannels = 2
        self.audio = pyaudio.PyAudio()
        audio_format = self.audio.get_format_from_width( sampwidth )
        self.stream = self.audio.open( format=audio_format,
                                  channels=nchannels,
                                  rate=cfg.samp_rate,
                                  output=True,
                                  stream_callback=self._callback )
        self.stream.start_stream()
        return None

    def end_stream(self):
        """turn off pyAudio stream"""
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        return None
