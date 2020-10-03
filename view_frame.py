"""
Steven Thomas (2020-09)
TODO: add licence/copyright note
"""

import numpy as np

import config as cfg

class ViewController( object ):

    def __init__( self, x_grid, y_grid, shape ):
        if x_grid is None:
            x_grid = np.arange( shape[1] )
        if y_grid is None:
            y_grid = np.arange( shape[0] )
        if (y_grid.size,x_grid.size) != shape:
            raise ValueError('grid spacing does not match shape.')
        self.shape = shape
        self.x_grid = x_grid
        self.y_grid = y_grid
        self.x_spacing = self._create_spacing( x_grid, cfg.x_pad )
        self.y_spacing = self._create_spacing( y_grid, cfg.y_pad )
        self.zoom_log = [(self.y_spacing,self.x_spacing)]
        return None

    def _create_spacing( self, grid, pad ):
        """grid = midpoint of gridcells (arbitrary scale)
        pad = fraction of screen to cut off each edge"""
        #special case if len(grid) == 1
        if grid.size == 1:
            return np.array([pad,1-pad])
        #calc/guess edges of gridcells
        edge = np.zeros( grid.size + 1 )
        edge[1:-1] = 0.5 * ( grid[:-1] + grid[1:] )
        edge[0] = 2*grid[0] - edge[1]
        edge[-1] = 2*grid[-1] - edge[-2]
        #get fraction for each gridcell (minus padding)
        width = abs( edge[:-1] - edge[1:] )
        scale = (1-2*pad) / width.sum()
        frac = width * scale
        spacing = np.concatenate(([pad],frac)).cumsum()
        return spacing

    def get_pos( self, x, y ):
        x_ind = self.x_spacing.searchsorted( x ) - 1
        if (x_ind == -1) or (x_ind == self.shape[1]):
            x_ind = None
        y_ind = self.y_spacing.searchsorted( y ) - 1
        if (y_ind == -1) or (y_ind == self.shape[0]):
            y_ind = None
        return (x_ind, y_ind)

    def zoom_in( self, x, y ):
        #zoom in at x/y point
        x_zoom = ((1+cfg.zoom_lvl)*self.x_spacing
                  - cfg.zoom_lvl*x).clip(cfg.x_pad,1-cfg.x_pad)
        y_zoom = ((1+cfg.zoom_lvl)*self.y_spacing
                  - cfg.zoom_lvl*y).clip(cfg.y_pad,1-cfg.y_pad)
        self.zoom_log.append( (y_zoom, x_zoom,) )
        self.x_spacing = x_zoom
        self.y_spacing = y_zoom
        return None

    def zoom_out( self ):
        #revert one step in zoom log
        if len( self.zoom_log ) == 1:
            #already fully zoomed out
            return None
        self.zoom_log = self.zoom_log[:-1]
        self.x_spacing = self.zoom_log[-1][1]
        self.y_spacing = self.zoom_log[-1][0]
        return None

    def zoom_reset( self ):
        #zoom out as far as possible
        self.zoom_log = [ self.zoom_log[0] ]
        self.x_spacing = self.zoom_log[-1][1]
        self.y_spacing = self.zoom_log[-1][0]
        return None
