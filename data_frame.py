"""
Steven Thomas (2020-09)
TODO: add licence/copyright note
"""

import numpy as np

import config as cfg

# array[y,x]

#DataController:
#- 2 data arrays
#- 2 sound index arrays
#- 2 stipple arrays
#- 1 label array
#- i/j
#- update

class DataController( object ):

    def __init__( self, arr1, arr2, stip1, stip2, label, sound_func ):
        #create attributes to save
        self.x = None
        self.y = None
        self.shape = None
        self.data = []
        self.audio_index = []
        self.stipple = []
        self.label = None
        self.sound_func = sound_func

        #process data arrays
        if arr2 is None:
            arr2 = arr1
        for arr in [arr1,arr2]:
            arr = np.array( arr, dtype=float )
            ndim = len( arr.shape )
            if ndim == 1:
                arr = arr.reshape((1,-1))
            elif ndim > 2:
                raise ValueError('data has too many dimensions.')
            self.data.append( arr )
        if self.data[0].shape != self.data[1].shape:
            raise ValueError('arr1 & arr2 must have the same shape.')
        self.shape = self.data[0].shape

        #create audio index (-1 is silent)
        vmin = min( [ arr.min() for arr in self.data ] )
        vmax = max( [ arr.max() for arr in self.data ] )
        interval = (vmax-vmin)/float(cfg.nfreq)
        for data_arr in self.data:
            ind_arr = ((data_arr-vmin)/interval).astype(int)
            #max value in data array one too high
            ind_arr[ ind_arr==cfg.nfreq ] -= 1
            #reset any NaN's to -1 (silent mode)
            ind_arr[ np.isnan(data_arr) ] = -1
            self.audio_index.append( ind_arr )

        #process stipple array
        if stip1 is None:
            stip1 = np.zeros(self.shape, dtype=bool)
        if stip2 is None:
            stip2 = np.zeros(self.shape, dtype=bool)
        for stip_arr in [stip1,stip2]:
            stip_arr = np.array( stip_arr, dtype=bool )
            if len(stip_arr.shape) == 1:
                stip_arr = stip_arr.reshape((1,-1))
            if stip_arr.shape != self.shape:
                raise ValueError('stipple array shape is incorrect.')
            self.stipple.append( stip_arr )

        #process text label
        if label is None:
            self.label = np.zeros( self.shape, dtype=np.object_ )
            for i in range(self.shape[0]):
                for j in range(self.shape[1]):
                    v1 = self.data[0][i,j]
                    v2 = self.data[1][i,j]
                    if v1 == v2:
                        txt = '[{:},{:}] = {:.3}'.format(i,j,v1)
                    else:
                        txt = '[{:},{:}] = {:.3} | {:.3}'.format(i,j,v1,v2)
                    self.label[i,j] = txt
        else:
            label = np.array( label, dtype=np.object_ )
            if len(label.shape) == 1:
                label = label.reshape((1,-1))
            if label.shape != self.shape:
                raise ValueError('label array shape is incorrect.')
            self.label = label
        return None
    
    def update( self, new_x, new_y ):
        if (new_x != self.x) or (new_y != self.y):
            self.x = new_x
            self.y = new_y
            signal_list = []
            if (self.x is None) or (self.y is None):
                #cursor offscreen, mute both channels
                signal_list = [ [0,False,True], [0,False,True] ]
            else:
                for c in [0,1]:
                    index_val = self.audio_index[c][self.y,self.x]
                    stipple_val = self.stipple[c][self.y,self.x]
                    if index_val == -1:
                        #data is NaN, mute channel
                        signal_list.append( [0,False,True] )
                    else:
                        signal_list.append( [index_val, stipple_val, False] )
            self.sound_func( *signal_list )
        return None

    def get_label( self ):
        if (self.x is None) or (self.y is None):
            return 'cursor is offscreen.'
        else:
            return self.label[ self.y, self.x ]
