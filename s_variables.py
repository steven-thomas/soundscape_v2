'''
Started 21/7/2013

@author: Steven Thomas
'''

default_volume = 0.8
zoom_fac = 0.5
sound_dict_loc = ''
sound_dict_name = 'sound_dict'
num_of_sounds = 25
timeslice = 0.05
max_freq = 1400
min_freq_estimate = 350
rate = 44100

period = int(rate*timeslice)

min_freq = int(min_freq_estimate * timeslice) / timeslice
