'''
Started 21/7/2013

@author: Steven Thomas
'''
from alsaaudio import *
from struct import pack
import s_variables as sv
import numpy as np
import cPickle as pickle
import gtk, pygtk, gobject
import os, threading, Queue
pygtk.require('2.0')

#-------------------------------------------------------------------------------------------------
#                                      FUNCTIONS FOR INPUT
#-------------------------------------------------------------------------------------------------
def clean_sound_map(sound_map):
	if not isinstance( sound_map, (list, tuple, np.ndarray)):
		return None
	if not isinstance( sound_map, np.ndarray):
		sound_map = np.array(sound_map)
	if not (sorted(sound_map) == sound_map).all():
		return None

	if len(sound_map) == (sv.num_of_sounds):
		pass
	elif len(sound_map) == (sv.num_of_sounds + 1):
		sound_map = sound_map[:-1]
	elif len(sound_map) == (sv.num_of_sounds + 2):
		sound_map = sound_map[1:-1]
	else:
		return None

	return sound_map

def clean_coord_map(array_data, xy_out, orientation, screen_dim):
	if orientation == 'x':
		array_dim = array_data['width']
	if orientation == 'y':
		array_dim = array_data['height']

	if xy_out == None:
		if array_data['multiple_arrays']:
			xy0 = np.arange(array_dim[0]) + 0.5
			xy1 = np.arange(array_dim[1]) + 0.5
			xy_out = [xy0, xy1]
		else:
			xy_out = np.arange(array_dim) + 0.5

	if not array_data['multiple_arrays']:
		spacing = make_spacing(xy_out)
		xy_map = make_xy_map(spacing, array_dim, screen_dim)
		if xy_map == None:
			return None, None
	else:
		if len(xy_out) != 2:
			if array_dim[0] != array_dim[1]:
				return None, None
			spacing = make_spacing(xy_out)
			xy0 = make_xy_map(spacing, array_dim[0], screen_dim)
			xy1 = make_xy_map(spacing, array_dim[1], screen_dim)
			xy_map = [xy0, xy1]
		else:
			spacing0 = make_spacing(xy_out[0])
			spacing1 = make_spacing(xy_out[1])
			xy0 = make_xy_map(spacing0, array_dim[0], screen_dim)
			xy1 = make_xy_map(spacing1, array_dim[1], screen_dim)
			xy_map = [xy0, xy1]
		if None in xy_map:
			return None, None
	return xy_out, xy_map

def make_spacing(xy_out):
	if not (sorted(xy_out) == xy_out).all():
		return None
	dist1 = float(xy_out[1] - xy_out[0])/2
	dist2 = float(xy_out[-1] - xy_out[-2])/2
	first = xy_out[0] - dist1
	last  = xy_out[-1] + dist2
	spacing = [first]
	for i in range(len(xy_out) - 1):
		spacing.append(float(xy_out[i+1]-xy_out[i])/2 + xy_out[i])
	spacing.append(last)
	return spacing

def make_xy_map(spacing, array_dim, screen_dim):
	if spacing == None:
		return None
	if len(spacing) != array_dim + 1:
		print 'incorrect length'
		return None
	size = (spacing[-1] - spacing[0])
	spacing_percent = [(i-spacing[0])/float(size) for i in spacing[1:]]
	xy_map = [np.searchsorted(spacing_percent,float(i)/screen_dim) \
	          for i in range(screen_dim)]
	return xy_map

def clean_stipple(array_data, stipple):
	if stipple == None:
		if array_data['multiple_arrays']:
			s0 = np.zeros_like(array_data['values'][0])
			s1 = np.zeros_like(array_data['values'][1])
			stipple = [s0, s1]
		else:
			stipple = np.zeros_like(array_data['values'])
	else:
		if not isinstance( stipple, (list, tuple, np.ndarray)):
			return None
		if len(stipple) == 0:
			return None

		if len(stipple) == 2:
			s0 = convert_array(stipple[0])
			s1 = convert_array(stipple[1])
		else:
			s0 = convert_array(stipple)
			s1 = None

		if not array_data['multiple_arrays']:
			if s1 != None:
				return None
			elif array_data['values'].shape != s0.shape:
				return None
			else:
				stipple = s0
		else:
			if array_data['values'][0].shape != s0.shape:
				return None
			if s1 == None:
				if array_data['values'][1].shape != s0.shape:
					return None
				else:
					stipple = [s0, s0]
			elif array_data['values'][1].shape != s1.shape:
				return None
			else:
				stipple = [s0, s1]
	return stipple

def clean_input(input_args):
	array_data = {}
	if not isinstance( input_args, (list, tuple, np.ndarray)):
		return None
	if len(input_args) == 0:
		return None

	if len(input_args) == 2:
		#assume 2 arrays
		array_data['multiple_arrays'] = True
		a0 = convert_array(input_args[0])
		a1 = convert_array(input_args[1])
		array_data['values'] = [a0, a1]
		array_data['width']  = [a0.shape[1], a1.shape[1]]
		array_data['height'] = [a0.shape[0], a1.shape[0]]
		array_data['min']    = [a0.min(), a1.min()]
		array_data['max']    = [a0.max(), a1.max()]
	else:
		#assume 1 array
		array_data['multiple_arrays'] = False
		array_data['values'] = convert_array(input_args)
		array_data['width']  = array_data['values'].shape[1]
		array_data['height'] = array_data['values'].shape[0]
		array_data['min']    = array_data['values'].min()
		array_data['max']    = array_data['values'].max()
		
	return array_data

def convert_array(data):
	#data is single matrix (type list, tuple, or numpy array)
	#convert to desired layout
	if isinstance( data[0], (list, tuple, np.ndarray)):
		#data is 2d
		if isinstance( data, np.ndarray):
			#data already ndarray
			array = data
		else:
			array = np.array(data)
	else:
		array = np.array([list(data)])
	return array

#-------------------------------------------------------------------------------------------------
#                                    FUNCTIONS FOR ALSAAUDIO
#-------------------------------------------------------------------------------------------------
class audio_thread(threading.Thread):
	def __init__(self, queue):
		super(audio_thread, self).__init__()
		self.queue = queue
		self.quit = False

		filepath = os.path.join(sv.sound_dict_loc, sv.sound_dict_name)
		file = open(filepath, 'r')
		self.sounds = pickle.load(file)
		file.close()

		self.out = PCM(type=PCM_PLAYBACK, mode=PCM_NORMAL, card='default')
		self.out.setformat(PCM_FORMAT_S32_LE)
		return None

	def run(self):
		s = zip(self.sounds['0'],self.sounds[str(sv.num_of_sounds)])
		s = [item for sublist in s for item in sublist]
		sound = pack('<'+2*sv.period*'l',*s)
		while not self.quit:
			if not self.queue.empty():
				keys = self.queue.get()
				s = zip(self.sounds[keys[0]],self.sounds[keys[1]])
				s = [item for sublist in s for item in sublist]
				sound = pack('<'+2*sv.period*'l',*s)
			self.out.write(sound)
		self.out.close()
		return None

#-------------------------------------------------------------------------------------------------
#                                      FUNCTIONS FOR PYGTK
#-------------------------------------------------------------------------------------------------
def zoom_in(xy_map, xy_pos):
	output = [xy_map[xy_pos - (2+i)/2] for i in range(xy_pos)]
	output.reverse()
	for i in range(len(xy_map) - xy_pos):
		output.append(xy_map[xy_pos + i/2])
	return output

def key_press_callback(window, event, array_data):
	if event.keyval == gtk.keysyms.minus:
		array_data['x_map'] = [x for x in array_data['original_x_map'] ]
		array_data['y_map'] = [y for y in array_data['original_y_map'] ]

	if event.keyval == gtk.keysyms.plus:
		x_pos, y_pos = window.get_pointer()
		width  = gtk.gdk.screen_width()
		height = gtk.gdk.screen_height()
		x_pos = max(x_pos, 0)
		x_pos = min(x_pos, width)
		y_pos = max(y_pos, 0)
		y_pos = min(y_pos, height)

		array_data['x_map'] = zoom_in(array_data['x_map'], x_pos)
		array_data['y_map'] = zoom_in(array_data['y_map'], y_pos)

	if event.keyval == gtk.keysyms.space:
		x_pos, y_pos = window.get_pointer()
		if array_data['multiple_arrays']:
			x0 = array_data['x_map'][0][x_pos]
			y0 = array_data['y_map'][0][y_pos]
			x1 = array_data['x_map'][1][x_pos]
			y1 = array_data['y_map'][1][y_pos]
			print array_data['x_out'][x0],', ',
			print array_data['y_out'][y0],': ',
			print array_data['values'][y0,x0],'; ',
			print array_data['x_out'][x1],', ',
			print array_data['y_out'][y1],': ',
			print array_data['values'][y1,x1]
		else:
			x = array_data['x_map'][x_pos]
			y = array_data['y_map'][y_pos]
			print array_data['x_out'][x],', ',
			print array_data['y_out'][y],': ',
			print array_data['values'][y,x]

	if event.keyval == gtk.keysyms.Return:
		gtk.main_quit()

	if event.keyval == gtk.keysyms.Escape:
		gtk.main_quit()
	return None

def mouse_move_callback(window, event, array_data):
	x_pos, y_pos = window.get_pointer()
	width  = gtk.gdk.screen_width()
	height = gtk.gdk.screen_height()
	x_pos = max(x_pos, 0)
	x_pos = min(x_pos, width)
	y_pos = max(y_pos, 0)
	y_pos = min(y_pos, height)

	if array_data['multiple_arrays']:
		x = array_data['x_map'][0][x_pos]
		y = array_data['y_map'][0][y_pos]
		value = array_data['values'][0][y,x]
		index1 = str(np.searchsorted(array_data['sound_map'], value))
		if array_data['stipple'][0][y,x]:
			index1 = 's' + index1

		x = array_data['x_map'][1][x_pos]
		y = array_data['y_map'][1][y_pos]
		value = array_data['values'][1][y,x]
		index2 = str(np.searchsorted(array_data['sound_map'], value))
		if array_data['stipple'][1][y,x]:
			index2 = 's' + index2

		key = [index1, index2]
		if array_data['queue'].empty():
			array_data['queue'].put(key)
	else:
		x = array_data['x_map'][x_pos]
		y = array_data['y_map'][y_pos]
		value = array_data['values'][y,x]
		index = str(np.searchsorted(array_data['sound_map'], value))
		if array_data['stipple'][y,x]:
			index = 's' + index
		key = [index, index]
		if array_data['queue'].empty():
			array_data['queue'].put(key)
	return None

#-------------------------------------------------------------------------------------------------
#                                   FUNCTIONS FOR SOUND WAVE DICT
#-------------------------------------------------------------------------------------------------
def make_wave(freq, max_amp=None):
	if max_amp == None:
		max_amp = (pow(2,31)-1) * np.exp((sv.min_freq / freq) - 1)
	wave = [max_amp * np.sin((2*np.pi*float(i)*freq) / sv.rate) for i in range(sv.period)]
	return np.array(wave)

def make_sound_dict():
	sounds = {}
	stipple_wave = make_wave(0.5/sv.timeslice, max_amp=1.0)
	
	for i in range(sv.num_of_sounds+1):
		curve_point = sv.min_freq * (sv.max_freq/sv.min_freq)**(float(i)/sv.num_of_sounds)
		margin = (curve_point - sv.min_freq) % (1/sv.timeslice)
		if margin > (0.5/sv.timeslice):
			margin -= 1/sv.timeslice
		wave = make_wave(curve_point-margin)
		sounds[str(i)] = wave.tolist()
		sounds['s'+str(i)] = (wave * stipple_wave).tolist()

	fileplace = os.path.join(sv.sound_dict_loc, sv.sound_dict_name)
	file = open(fileplace, 'w')
	pickle.dump(sounds, file)
	file.close()
	return None

#-------------------------------------------------------------------------------------------------
#                                    FUNCTIONS FOR DEBUGGING
#-------------------------------------------------------------------------------------------------
def debug_printing(array_data, width, height):
	print array_data.keys()
	print 'matrix shape: ',
	print array_data['values'].shape
	print 'width: ',
	print array_data['width']
	print 'height: ',
	print array_data['height']
	print 'x_map'
	for i in set(array_data['x_map']):
		print (str(i)+' count: '),
		print array_data['x_map'].index(i)
	print 'y_map'
	for i in set(array_data['y_map']):
		print (str(i)+' count: '),
		print array_data['y_map'].index(i)
	print 'sound map: ',
	print array_data['sound_map']
	return None
