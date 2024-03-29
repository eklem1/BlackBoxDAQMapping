"""
Emma Klemets, Mar 2023

Code to use with a stick mapper set up, taking data in intervals, taking user input
to label each data set with a corresponding distance. All data will be saved in a sub
folder created in ./data/ labeled by the date.

Requires the installation for LabJackT7 found at: https://github.com/ucn-triumf/labjack_mag_readout
"""

from labjack import ljm
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import pandas as pd
from tqdm import tqdm
from io import StringIO
import os

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


def to_csv_header(LJ_object, filename, GeometrySetUp, msg = '', idx=-1):
	"""
	Create the header for the summary stats data file
	"""

	# write file header

	header = [  f'# labjack output summary file',
		f'# {msg}',
		 '# Settings:',
		f'#   DEVICE_TYPE:              {LJ_object.DEVICE_TYPE}',
		f'#   CONNECTION_TYPE:          {LJ_object.CONNECTION_TYPE}',
		f'#   IP:                       {LJ_object.IP}',
		f'#   NumDataPoints:            {GeometrySetUp["N"]}',
		f'#   l_out:                    {GeometrySetUp["length of tube out"]}',
		f'#   l_scm:                    {GeometrySetUp["distance from center of SCM to MSR wall"]}',
		f'#   FG number:                {GeometrySetUp["FG_num"]}',
		f'#   FG type:                	{GeometrySetUp["FG_type"]}',
		f'#   B0coil Current:           {GeometrySetUp["B0coil_Current"]}',
		f'#   B0coil Voltage:           {GeometrySetUp["B0coil_Voltage"]}',
		f'#   SCMcoil Current:          {GeometrySetUp["SCMcoil_Current"]}',
		f'#   SCMcoil Voltage:          {GeometrySetUp["SCMcoil_Voltage"]}',
		f'#   Saddlecoil Current:       {GeometrySetUp["Saddlecoil_Current"]}',
		f'#   Solenoidcoil Current:     {GeometrySetUp["Solenoidcoil_Current"]}',
		]

	header.extend([f'#   {key}:' + ' '*(25-len(key)) + f'{val}' 
	for key, val in LJ_object.STREAM_SETTINGS.items()])

	header.extend([ f'# Scan rate of last read:    {set_scan_rate} Hz',
		'#',
		f'# File started at {datetime.now()}',
		'# \n'
		])

	with open(filename, 'w') as fid:
		fid.write('\n'.join(header))
	return


def to_csv_stats(distance, LJ_object, filename):
	"""
	Write summary data for a single distance to a csv

	filename: name of file to write to

	"""

	# check that data exists
	if len(LJ_object.data) == 0:
		raise RuntimeError('No data saved')
		idx = -1
	else:
		idx = 0

	means = LJ_object.data[-1].mean()
	#changed to ddof=1, so I am using the unbiased estimator of the std
	std = LJ_object.data[-1].std( ddof=1) 
	#I'm just going to include N from now on, so you can do this later
	#for early files

	cols = [['time [s]', 'distance [cm]']]
	cols.append(LJ_object.data[-1].columns.values+ ' mean')
	cols.append(LJ_object.data[-1].columns.values+ ' std')

	cols =  np.array([item for sublist in cols for item in sublist])

	saveStats = np.array([LJ_object.stream_times[-1], distance])
	saveStats = np.concatenate((saveStats, means))
	saveStats = np.concatenate((saveStats, std))
	saveStats = [saveStats.flatten()]

	stats_df = pd.DataFrame(data=saveStats, columns=cols) 
	stats_df = stats_df.set_index('time [s]')

	if len(LJ_object.data) == 1:
		#no data yet, so include the column names
		stats_df.to_csv(filename, mode='a+', header=True)
	else:
		#there is data already in the file, only save data
		stats_df.to_csv(filename, mode='a+', header=False)

	return


############## Set up of the labjack and file names ##############
set_scan_rate = 100 #Hz
set_scan_length = 500 #number of scans
set_nreads = 1 #number of times you repeat the scan

#set the name of the file to be used to collect the stats of the data
now = datetime.now()
timeStamp = now.strftime("%Y%m%d_%H%M%S")
dayStamp = now.strftime("%Y-%m-%d")

#the folder where all the data will be saved
folder = f'./data/{dayStamp}/'
#make the folder if it doesn't exist yet
os.makedirs(folder, exist_ok=True)  

StatsFileName = f'{folder}{timeStamp}_testStats.csv'
#flag to add into each individual data file's name
dataFlag = ''

############## Set up of your set up geometry ##############
#right now this you have to input yourself here
l_tube_out = 89.75 #cm
l_SCM = 43.0 #52.4 #cm
FG_num = [410, 409] #could be a list if you were using multiple FGs
FG_type = [1000, 1000] #could be a list if you were using multiple FGs

B0coil_Current = None #mV
B0coil_Voltage = None #mV
SCMcoil_Current = None
SCMcoil_Voltage = None #V
Saddlecoil_Current = None #A
Solenoidcoil_Current = None #A

# a message to put in your header (new lines should start with a # )
msg = 'Data taken with Mag690-FL1000 #410,\n'+ \
		'# miniMSR degaussed with miniB0 on, but badly. All coils off.'#+\
		'# miniB0 powered with function generator (set to output 2.87V, but b0 sees 74.4mV)'


GeometrySetUp = {
	"N": set_scan_length*set_nreads,
	"length of tube out": l_tube_out, 
	"distance from center of SCM to MSR wall": l_SCM, 
	"FG_num": FG_num,
	"FG_type": FG_type,
	"B0coil_Current": B0coil_Current,
	"B0coil_Voltage": B0coil_Voltage,
	"SCMcoil_Current": SCMcoil_Current,
	"SCMcoil_Voltage": SCMcoil_Voltage,
	"Saddlecoil_Current": Saddlecoil_Current,
	"Solenoidcoil_Current": Solenoidcoil_Current,
}


############## Main code ##############
def main(e):
	print( "All individual data will be saved to files starting with "+
		f"`{timeStamp}_data{dataFlag}`, and the final stats file is `{StatsFileName}`.\n"
		f"Each data point is set to take data for {set_scan_length/set_scan_rate} s, at {set_scan_rate} Hz.\n"+
		"Enter 'exit' to end the program.\n"+
		"Press enter to start your data taking!"
		)

	############## Connect to the labjack ##############
	#make labjack reader object

	#right now just reading one FG channel, but you can put more here
	# FG 1 for data taking; FG 2 for enviroment montioring
	LJ_obj = lj.LabJackT7(channel_list=[1, 2])

	#uncomment for direct UBC connection to the Black DAQ box
	LJ_obj.CONNECTION_TYPE = 'USB'
	LJ_obj.IP = 'ANY'

	#try to connect  - should add a try-except here
	LJ_obj.connect()

	#write the header of the stats file
	to_csv_header(LJ_obj, StatsFileName, GeometrySetUp, msg)

	############## Take data ##############
	while not e.is_set():

		# '''
		while True and not e.is_set():
			# enter a position - try until a valid input is submitted
			#code from https://stackoverflow.com/questions/23294658/asking-the-user-for-input-until-they-give-a-valid-response
			try:
				distanceToSet = float(input("Enter your value: "))

			except ValueError:
				print("Not a valid float (needs to be in cm).")
				#better try again... Return to the start of the loop
				continue
			else:
				#we're ready to exit the loop.
				break

		if not e.is_set():
			print(f"Taking data for d={distanceToSet} cm in:")
			# countdown(1)
			# '''

			# collect data
			times_all, df_all = LJ_obj.read(scan_rate=set_scan_rate, scan_length=set_scan_length, 
											nreads=set_nreads, save=True)

			# Save just the data just taken to a file
			LJ_obj.to_csv(f"{folder}{timeStamp}_data{dataFlag}_d={distanceToSet}.csv", idx=-1)
			print("Done")

		# finish
		# calculate/save averages, stats and save to file
		to_csv_stats(distanceToSet, LJ_obj, StatsFileName)

	print('Exiting')
	LJ_obj.disconnect()


# This containts the code to end the program
# from https://stackoverflow.com/questions/65595027/how-to-interrupt-python-program-on-user-input
e = threading.Event()

main_thread = threading.Thread(name='main program', target=main, args=(e,))

#start the main code, above
main_thread.start()

#but then also start this second thread of code, and add it on so they run at the same time
while True:
    if input().lower() == 'exit':
        print('Terminating program')
        e.set()
        break

main_thread.join()

