from labjack import ljm
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import pandas as pd
from tqdm import tqdm
from io import StringIO

import threading
import time

import LabJackT7 as lj

def countdown(secs):
	"""
	Makes a little countdown

	Inspired from
	https://www.programiz.com/python-programming/examples/countdown-timer
	"""
	while secs:
		secs = secs
		timeformat = '{:02d}'.format(secs)
		print(timeformat, end='\r')
		time.sleep(1)
		secs -= 1

	print("Taking data")
	return


def to_csv_header(LJ_object, filename, idx=-1):
	"""
	Create the header for the summary data file
	"""

	# write file header
    if idx < 0: msg = 'multiple reads of stream'
    else:       msg = 'single read of stream'
        
    header = [  f'# labjack output {msg}',
                '# Settings:',
                f'#   DEVICE_TYPE:              {LJ_object.DEVICE_TYPE}',
                f'#   CONNECTION_TYPE:          {LJ_object.CONNECTION_TYPE}',
                f'#   IP:                       {LJ_object.IP}',
             ]
    header.extend([f'#   {key}:' + ' '*(25-len(key)) + f'{val}' 
                   for key, val in LJ_object.STREAM_SETTINGS.items()])
    
    header.extend([ f'# Scan rate of last read:    {LJ_object.scan_rate} Hz',
                    '#',
                    f'# File started at {datetime.now()}',
                    '# \n'
                  ])
    
    with open(filename, 'w') as fid:
        fid.write('\n'.join(header))


def to_csv_stats(distance, LJ_object, filename, idx=-1):
	"""
	Write summary data for a single distance to a csv

	filename: name of file to write to

	"""

	if len(LJ_object.data) == 1:
		idx = 0

	# check that data exists
	if len(LJ_object.data) == 0:
		raise RuntimeError('No data saved')


	# write a single stream
	if idx >= 0:

		# print(LJ_obj.data[-1])

		means = LJ_obj.data[-1].mean()
		std = LJ_obj.data[-1].std()

		stats_data = pn.array([distance, means, std, LJ_object.stream_times[-1]])
		print(stats_data)


		# with open(filename, 'a+') as fid:
		#     fid.write(f'# START stream {self.stream_times[idx]}\n#\n')

		# self.data[idx].to_csv(filename, mode='a+', header=False)

	else:
		print("Not inplemented for multiple streams.")

	return


def main(e):

	############## Set up of the labjack ##############
	#make labjack reader object

	#right now just reading one FG channel
	LJ_obj = lj.LabJackT7(channel_list=[1])

	#try to connect
	LJ_obj.connect()

	set_scan_rate = 100 #Hz
	set_scan_length = 50 #500 #number of scans
	set_nreads = 1 #number of times you repeat the scan

	############## Take data ##############
	while not e.is_set():
		#pass

		# loop
		# enter a position
		distanceToSet = 5
		'''
		while True and not e.is_set():
			#code from https://stackoverflow.com/questions/23294658/asking-the-user-for-input-until-they-give-a-valid-response
			try:
				# Note: Python 2.x users should use raw_input, the equivalent of 3.x's input
				distanceToSet = float(input("Enter your value: "))

			except ValueError:
				print("Not a valid float (needs to be in cm).")
				#better try again... Return to the start of the loop
				continue
			else:
				#age was successfully parsed!
				#we're ready to exit the loop.
				break

		print(f"Taking data for d={distanceToSet} cm in:")
		countdown(5)
		'''

		# collect data
		times_all, df_all = LJ_obj.read(scan_rate=set_scan_rate, scan_length=set_scan_length, 
										nreads=set_nreads, save=True)

		LJ_obj.to_csv(f"data_d={distanceToSet}.csv")
		print("Done")

		to_csv_stats(distanceToSet, LJ_obj, 'test1.csv', idx=-1)


		# finish
		# calculate/save averages, stats

		#save all the above to a file (or two files)


	print('Exiting')
	LJ_obj.disconnect()
	# Add some possible cleanup code here

# This containts the code to end the program
# from https://stackoverflow.com/questions/65595027/how-to-interrupt-python-program-on-user-input
e = threading.Event()

main_thread = threading.Thread(name='main program',
                               target=main, args=(e,))

#start the main code, above
main_thread.start()

#but then also start this second thread of code, and add it on so they run at the same time
while True:
    if input().lower() == 'exit':
        print('Terminating program')
        e.set()
        break

main_thread.join()

