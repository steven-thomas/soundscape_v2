"""
Steven Thomas (2020-09)
TODO: add licence/copyright note
"""

import numpy as np
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk

class InterfaceController( object ):

    def __init__( self, data, view ):
        
        self.data = data
        self.view = view
        #setup main gtk window
        self.window = Gtk.Window()
        self.window.set_title( "soundscape" )
        self.window.fullscreen()
        self.width  = Gdk.Screen.width()
        self.height = Gdk.Screen.height()
        
        #connect user input
        self.window.add_events( Gdk.EventMask.POINTER_MOTION_MASK )
        self.window.connect( "delete-event", Gtk.main_quit )
        self.window.connect( "motion-notify-event", self.mouse_move )
        self.window.connect( "key-press-event", self.zoom_in )
        self.window.connect( "key-press-event", self.zoom_out )
        self.window.connect( "key-press-event", self.zoom_reset )
        self.window.connect( "key-press-event", self.print_label )
        self.window.connect( "key-press-event", self.close_window )
        return None
    
    def start( self ):
        self.window.show_all()
        Gtk.main()
        return None

    def end( self ):
        self.window.destroy()
        Gtk.main_quit()
        return None

    def mouse_move( self, widget, event ):
        x_pix, y_pix = self.window.get_pointer()
        x_frac = float(x_pix) / float(self.width)
        y_frac = float(y_pix) / float(self.height)
        (x_ind, y_ind) = self.view.get_pos( x_frac, y_frac )
        self.data.update( x_ind, y_ind )
        return None

    def zoom_in( self, widget, event ):
        x_pix, y_pix = self.window.get_pointer()
        x_frac = float(x_pix) / float(self.width)
        y_frac = float(y_pix) / float(self.height)
        if event.keyval == Gdk.KEY_equal:
            self.view.zoom_in( x_frac, y_frac )
        return None
    
    def zoom_out( self, widget, event ):
        if event.keyval == Gdk.KEY_minus:
            self.view.zoom_out()
        return None

    def zoom_reset( self, widget, event ):
        if event.keyval == Gdk.KEY_0:
            self.view.zoom_reset()
        return None

    def print_label( self, widget, event ):
        if event.keyval == Gdk.KEY_space:
            text = self.data.get_label()
            print( text )
        return None

    def close_window( self, widget, event ):
        if ( (event.keyval == Gdk.KEY_Return) or (event.keyval == Gdk.KEY_Escape) ):
            self.window.destroy()
            Gtk.main_quit()
        return None
