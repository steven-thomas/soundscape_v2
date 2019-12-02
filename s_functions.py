'''
Started 21/7/2013

@author: Steven Thomas
'''
from alsaaudio import *
from struct import pack
import s_variables as sv
import numpy as np
import pickle
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk as gtk
from gi.repository import GObject as gobject
from gi.repository import Gdk as gdk
import os, threading

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

	if xy_out is None:
		if array_data['multiple_arrays']:
			xy0 = np.arange(array_dim[0]) + 0.5
			xy1 = np.arange(array_dim[1]) + 0.5
			xy_out = [xy0, xy1]
		else:
			xy_out = np.arange(array_dim) + 0.5
	else:
		if array_data['multiple_arrays']:
			if len(xy_out) == 2:
				if len(xy_out[0]) != array_dim[0] or len(xy_out[1]) != array_dim[1]:
					xy_out = None
			else:
				if len(xy_out) == array_dim[0] or len(xy_out) == array_dim[1]:
					new_out = [ i for i in xy_out ]
					xy_out = [new_out, new_out]
		else:
			if len(xy_out) != array_dim:
				xy_out = None

	xy_map = build_xy_mapping(array_data['multiple_arrays'], xy_out, screen_dim)
	xy_out = np.array( xy_out)
	return xy_out, xy_map

def build_xy_mapping(multiple_arrays, xy_out, screen_dim):
	if not multiple_arrays:
		spacing = make_spacing(xy_out)
		xy_map = make_xy_map(spacing, screen_dim)
		if xy_map is None:
			return None, None
	else:
		if len(xy_out) != 2:
			return None, None
		else:
			spacing0 = make_spacing(xy_out[0])
			spacing1 = make_spacing(xy_out[1])
			xy0 = make_xy_map(spacing0, screen_dim)
			xy1 = make_xy_map(spacing1, screen_dim)
			xy_map = [xy0, xy1]
	return xy_map

def make_spacing(xy_out):
	xy_out = np.array(xy_out)
	if not (sorted(xy_out) == xy_out).all():
		return None
	if len(xy_out) == 1:
		return [0, 1]
	dist1 = float(xy_out[1] - xy_out[0])/2
	dist2 = float(xy_out[-1] - xy_out[-2])/2
	first = xy_out[0] - dist1
	last  = xy_out[-1] + dist2
	spacing = [first]
	for i in range(len(xy_out) - 1):
		spacing.append(float(xy_out[i+1]-xy_out[i])/2 + xy_out[i])
	spacing.append(last)
	return spacing

def make_xy_map(spacing, screen_dim):
	if spacing is None:
		return None
	size = (spacing[-1] - spacing[0])
	spacing_percent = [(i-spacing[0])/float(size) for i in spacing[1:]]
	xy_map = [np.searchsorted(spacing_percent,float(i)/screen_dim) \
	          for i in range(screen_dim)]
	return xy_map

def clean_stipple(array_data, stipple):
	if stipple is None:
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
			if s1 is None:
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
		file = open(filepath, 'rb')
		self.sounds = pickle.load(file)
		file.close()

		self.out = PCM(type=PCM_PLAYBACK, mode=PCM_NORMAL, device='default')
		self.out.setformat(PCM_FORMAT_S32_LE)
		return None

	def run(self):
		s = list(zip(self.sounds['0'],self.sounds[str(sv.num_of_sounds)]))
		s = [int(item) for sublist in s for item in sublist]
		sound = pack('<'+2*sv.period*'l',*s)
		while not self.quit:
			if not self.queue.empty():
				keys = self.queue.get()
				s = list(zip(self.sounds[keys[0]],self.sounds[keys[1]]))
				s = [int(item) for sublist in s for item in sublist]
				sound = pack('<'+2*sv.period*'l',*s)
			self.out.write(sound)
		self.out.close()
		return None

#-------------------------------------------------------------------------------------------------
#                                      FUNCTIONS FOR PYGTK
#-------------------------------------------------------------------------------------------------
def key_press_callback(window, event, array_data):
	if event.keyval == gdk.KEY_minus:
		#total zoom out
		if array_data['multiple_arrays']:
			array_data['x_map'][0] = [x for x in array_data['original_x_map'][0] ]
			array_data['y_map'][0] = [y for y in array_data['original_y_map'][0] ]
			array_data['x_map'][1] = [x for x in array_data['original_x_map'][1] ]
			array_data['y_map'][1] = [y for y in array_data['original_y_map'][1] ]
		else:
			array_data['x_map'] = [x for x in array_data['original_x_map'] ]
			array_data['y_map'] = [y for y in array_data['original_y_map'] ]

	if event.keyval == gdk.KEY_equal:
		#zoom in
		x_pos, y_pos = window.get_pointer()
		width  = gdk.Screen.width()
		height = gdk.Screen.height()
		x_pos = max(x_pos, 1)
		x_pos = min(x_pos, width)
		y_pos = max(y_pos, 1)
		y_pos = min(y_pos, height)

		x_map =  array_data['x_map']
		y_map =  array_data['y_map']
		if array_data['multiple_arrays']:
			y_map[0].reverse()
			y_map[1].reverse()
		else:
			y_map.reverse()				#changes cartesian layout to array layout
		y_pos = height - y_pos				#When changing co-ord layout, pointer also moves

		x_min = int(x_pos * sv.zoom_fac)
		x_max = int(x_pos + ((width - x_pos) * sv.zoom_fac) )
		y_min = int(y_pos * sv.zoom_fac)
		y_max = int(y_pos + ((height - y_pos) * sv.zoom_fac) )

		if array_data['multiple_arrays']:
			x0_min = x_map[0][x_min]
			x1_min = x_map[1][x_min]
			x0_max = x_map[0][x_max]+1
			x1_max = x_map[1][x_max]+1
			y0_min = y_map[0][y_min]
			y1_min = y_map[1][y_min]
			y0_max = y_map[0][y_max]+1
			y1_max = y_map[1][y_max]+1

			nx_out = [array_data['x_out'][0][x0_min:x0_max], array_data['x_out'][1][x1_min:x1_max]]
			ny_out = [array_data['y_out'][0][y0_min:y0_max], array_data['y_out'][1][y1_min:y1_max]]
			x_rel_map = build_xy_mapping(True, nx_out, width)
			y_rel_map = build_xy_mapping(True, ny_out, height)
			x_map0 = [i + x0_min for i in x_rel_map[0]]
			x_map1 = [i + x1_min for i in x_rel_map[1]]
			y_map0 = [i + y0_min for i in y_rel_map[0]]
			y_map1 = [i + y1_min for i in y_rel_map[1]]
			x_map = [x_map0, x_map1]
			y_map = [y_map0, y_map1]
		else:
			x_min = x_map[x_min]
			x_max = x_map[x_max]+1
			y_min = y_map[y_min]
			y_max = y_map[y_max]+1

			nx_out = array_data['x_out'][x_min:x_max]
			ny_out = array_data['y_out'][y_min:y_max]
			x_rel_map = build_xy_mapping(False, nx_out, width)
			y_rel_map = build_xy_mapping(False, ny_out, height)
			x_map = [i + x_min for i in x_rel_map]
			y_map = [i + y_min for i in y_rel_map]

		if array_data['multiple_arrays']:
			y_map[0].reverse()
			y_map[1].reverse()
		else:
			y_map.reverse()				#changes array layout to cartesian layout
		array_data['x_map'] = x_map
		array_data['y_map'] = y_map

	if event.keyval == gdk.KEY_space:
		#data print out
		x_pos, y_pos = window.get_pointer()
		if array_data['multiple_arrays']:
			x0 = array_data['x_map'][0][x_pos]
			y0 = array_data['y_map'][0][y_pos]
			x1 = array_data['x_map'][1][x_pos]
			y1 = array_data['y_map'][1][y_pos]

			x_out_0 = str(array_data['x_out'][0][x0]) + ' , '
			y_out_0 = str(array_data['y_out'][0][y0]) + ' : '
			val_0   = str(array_data['values'][0][y0,x0]) + ' ; '
			x_out_1 = str(array_data['x_out'][1][x1]) + ' , '
			y_out_1 = str(array_data['y_out'][1][y1]) + ' : '
			val_1   = str(array_data['values'][1][y1,x1])
			
			if len(array_data['x_out'][0]) == 1:
				x_out_0 = ''
			if len(array_data['x_out'][1]) == 1:
				x_out_1 = ''
			if len(array_data['y_out'][0]) == 1:
				x_out_0 = x_out_0.replace(',',':')
				y_out_0 = ''
			if len(array_data['y_out'][1]) == 1:
				x_out_1 = x_out_1.replace(',',':')
				y_out_1 = ''

			if (array_data['x_out'][0] == array_data['x_out'][1]).all():
				if (array_data['y_out'][0] == array_data['y_out'][1]).all():
					x_out_1 = ''
					y_out_1 = ''

			#print  x_out_0 + y_out_0 + val_0 + x_out_1 + y_out_1 + val_1
		else:
			x = array_data['x_map'][x_pos]
			y = array_data['y_map'][y_pos]

			x_out = str(array_data['x_out'][x]) + ' , '
			y_out = str(array_data['y_out'][y]) + ' : '
			val   = str(array_data['values'][y,x])

			if len(array_data['x_out']) == 1:
				x_out = ''
			if len(array_data['y_out']) == 1:
				x_out = x_out.replace(',',':')
				y_out = ''

			#print x_out + y_out + val

	if event.keyval== gdk.KEY_Return:
		gtk.main_quit()

	if event.keyval == gdk.KEY_Escape:
		gtk.main_quit()
	return None

def mouse_move_callback(window, event, array_data):
	x_pos, y_pos = window.get_pointer()
	width  = gdk.Screen.width()
	height = gdk.Screen.height()
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
def make_wave(freq, volume=None):
	if volume == None:
		amp = 1.0
	else:
		max_amp = (pow(2,31)-1) * np.exp((sv.min_freq / freq) - 1)
		amp = max_amp * volume
	wave = [amp * np.sin((2*np.pi*float(i)*freq) / sv.rate) for i in range(sv.period)]
	return np.array(wave)

def make_sound_dict(volume):

	sounds = {}
	stipple_wave = make_wave(0.5/sv.timeslice)
	
	for i in range(sv.num_of_sounds+1):
		curve_point = sv.min_freq * (sv.max_freq/sv.min_freq)**(float(i)/sv.num_of_sounds)
		margin = (curve_point - sv.min_freq) % (1/sv.timeslice)
		if margin > (0.5/sv.timeslice):
			margin -= 1/sv.timeslice
		wave = make_wave(curve_point-margin, volume)
		sounds[str(i)] = wave.tolist()
		sounds['s'+str(i)] = (wave * stipple_wave).tolist()

	fileplace = os.path.join(sv.sound_dict_loc, sv.sound_dict_name)
	file = open(fileplace, 'wb')
	pickle.dump(sounds, file)
	file.close()
	return None

#-------------------------------------------------------------------------------------------------
#                                    FUNCTIONS FOR DEBUGGING
#-------------------------------------------------------------------------------------------------
def debug_printing(array_data):
	#print array_data.keys()
	if array_data['multiple_arrays']:
		pass
	else:
		#print 'map zoomed:',
		#print not array_data['original_y_map'] == array_data['y_map']
		#print 'y_map values:'
		cur_val = array_data['y_map'][0]
		start = 0
		for i in range(len(array_data['y_map'])):
			val = array_data['y_map'][i]
			if val != cur_val:
				#print str(cur_val)+': '+str(start)+'-'+str(i)
				cur_val = val
				start = i
		#print str(array_data['y_map'][-1])+': '+str(start)+'-'+str(len(array_data['y_map']))

		#print '\n'
		#print 'original_y_map values:'
		cur_val = array_data['original_y_map'][0]
		start = 0
		for i in range(len(array_data['original_y_map'])):
			val = array_data['original_y_map'][i]
			if val != cur_val:
				#print str(cur_val)+': '+str(start)+'-'+str(i)
				cur_val = val
				start = i
		#print str(array_data['original_y_map'][-1])+': '+str(start)+'-'+str(len(array_data['original_y_map']))
		#print '\n'

		"""
		#print 'matrix shape: ',
		#print array_data['values'].shape
		#print 'width: ',
		#print array_data['width']
		#print 'height: ',
		#print array_data['height']
		#print 'x_map'
		for i in set(array_data['x_map']):
			#print (str(i)+' count: '),
			#print array_data['x_map'].index(i)
		#print 'y_map'
		for i in set(array_data['y_map']):
			#print (str(i)+' count: '),
			#print array_data['y_map'].index(i)
		#print 'values: ',
		#print array_data['values']
		"""
	return None
