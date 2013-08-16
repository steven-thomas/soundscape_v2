'''
Started 21/7/2013

@author: Steven Thomas
'''
from alsaaudio import *
from struct import pack
import s_functions as sf
import s_variables as sv
import numpy as np
import cPickle as pickle
import pygtk, gtk, gobject
import sys, os
import threading, Queue

pygtk.require('2.0')
gobject.threads_init()
gtk.gdk.threads_init()

def soundscape(input_args, x_out=None, y_out=None, sound_map=None, stipple=None):
	#clean input
	array_data = sf.clean_input(input_args)
	if array_data == None:
		raise StandardError("input_args incorrect")

	#setup sound dict if not already setup
	filepath = os.path.join(sv.sound_dict_loc, sv.sound_dict_name)
	if not os.access(filepath, 0):
		sf.make_sound_dict()

	#setup user interface
	main_window = gtk.Window()
	main_window.add_events(gtk.gdk.POINTER_MOTION_MASK)
	main_window.set_title("soundscape")
	main_window.fullscreen()
	screen_width  = gtk.gdk.screen_width()
	screen_height = gtk.gdk.screen_height()

	#setup optional args
	stipple = sf.clean_stipple(array_data, stipple)
	if stipple == None:
		raise StandardError("invalid stipple value")
	array_data['stipple'] = stipple

	x_out, x_map = sf.clean_coord_map(array_data, x_out, 'x', screen_width)
	if x_out == None:
		raise StandardError("invalid x out value")
	array_data['x_out'] = x_out
	array_data['x_map'] = x_map

	y_out, y_map = sf.clean_coord_map(array_data, y_out, 'y', screen_height)
	if y_out == None:
		raise StandardError("invalid y out value")
	array_data['y_out'] = y_out
	array_data['y_map'] = y_map

	array_data['original_x_map'] = x_map
	array_data['original_y_map'] = y_map

	if sound_map == None:
		if array_data['multiple_arrays']:
			top = max(array_data['max'])
			bot = min(array_data['min'])
		else:
			top = array_data['max']
			bot = array_data['min']
		a = np.linspace(bot, top, num=(sv.num_of_sounds+1), endpoint=False)
		sound_map = a[1:]
	else:
		sound_map = sf.clean_sound_map(sound_map)
		if sound_map == None:
			raise StandardError("invalid sound map value")
	array_data['sound_map'] = sound_map

	array_data['queue'] = Queue.Queue()

	#DEBUG PRINTING
	#sf.debug_printing(array_data, screen_width, screen_height)

	
	#connect user input
	main_window.connect("delete-event", gtk.main_quit)
	main_window.connect("key-press-event", sf.key_press_callback, array_data)
	main_window.connect("motion-notify-event", sf.mouse_move_callback, array_data)
	main_window.show_all()

	#run sound and screen
	t = sf.audio_thread(array_data['queue'])
	t.start()
	gtk.main()

	#close program when gtk.main quits
	t.quit = True
	main_window.destroy()
	return None
	
