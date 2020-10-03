"""
Steven Thomas (2020-09)
TODO: add licence/copyright note
"""

import numpy as np
from audio import AudioController
from data_frame import DataController
from view_frame import ViewController
from interface import InterfaceController

def soundscape( arr1, arr2=None, x_grid=None, y_grid=None,
                stip1=None, stip2=None, label=None ):
    """
    arr1 = data to send to channel 1
    arr2 = data to send to channel 2 (optional)
    x_loc = x-coordinates of gridcell centers (default to uniform)
    y_loc = y-coordinates of gridcell centers (default to uniform)
    stip1 = stipple mask for arr1
    stip2 = stipple mask for arr2
    label = print label for each gridcell
    """
    audio = AudioController()
    data = DataController( arr1, arr2, stip1, stip2, label, audio.update )
    view = ViewController( x_grid, y_grid, data.shape )
    main_window = InterfaceController( data, view )

    audio.start_stream()
    main_window.start()

    main_window.end()
    audio.end_stream()
    return None
