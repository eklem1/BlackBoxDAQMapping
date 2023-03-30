from labjack import ljm
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import pandas as pd
from tqdm import tqdm
from io import StringIO

# import sys, os
# sys.path.insert(1, '../labjack_mag_readout/')
import LabJackT7 as lj

#make labjack reader object
LJ_obj = lj.LabJackT7(channel_list=[10])

#try to connect
LJ_obj.connect()

#live time continusous drawing
# LJ_obj.draw(scan_rate=1000, scan_duration=2)
# """
set_scan_rate = 100 #Hz
set_scan_length = 10 #number of scans
set_nreads = 1 #number of times you repeat the scan

print(f"Getting data for {set_scan_length/set_scan_rate} s, "+
f"{set_nreads} time(s) -> total of {set_nreads*set_scan_length/set_scan_rate} s")

times_all, df_all = LJ_obj.read(scan_rate=set_scan_rate, scan_length=set_scan_length, 
	nreads=set_nreads, save=True)

print(times_all, df_all)
# """
# LJ_obj.to_csv("test.csv")
# LJ_obj.to_csv("SineZ_1Hz_5Vpp.csv")

"""
LJ_obj.read(scan_rate=1500, scan_length=100, nreads=1, save=True)
LJ_obj.draw(scan_rate=1500, scan_duration=1)

LJ_obj.to_csv(filename, idx=-1)
"""

LJ_obj.disconnect()