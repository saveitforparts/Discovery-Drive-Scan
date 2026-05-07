#Python program to scan with Discovery Drive and output signal strength array
#Process output into bitmap with dd_image.py
#Version 1.0
#Gabe Emerson / Saveitforparts 2026, Email: gabe@saveitforparts.com

import socket
import sys
import time
import regex as re
import numpy as np
from rtlsdr import RtlSdr
from pylab import *
import argparse
import subprocess

#accept command-line variables, if any
parser = argparse.ArgumentParser()
parser.add_argument("-as", "--azimuthstart", help="beginning of azimuth range")
parser.add_argument("-ae", "--azimuthend", help="end of azimuth range")
parser.add_argument("-es", "--elevationstart", help="beginning of elevation range")
parser.add_argument("-ee", "--elevationend", help="end of elevation range")
parser.add_argument("-f", "--frequency", help="frequency for scan")
parser.add_argument("-bt", "--biastee", help="bias_tee on(1) or off (0)")
parser.add_argument("-g", "--gain", help="desired gain (will be rounded to nearast available)")
parser.add_argument("-p", "--preview", help="preview image on(1) or off(0)")
#parser.add_argument("-i", "--integration", help="integration time (256, 512, 1024, etc)")
parser.add_argument("-bw", "--bandwidth", help="bandwidth in kHz")
args = parser.parse_args()
if not args.azimuthstart == None:
	az_start = int(args.azimuthstart)
if not args.azimuthend == None:
	az_end = int(args.azimuthend)
if not args.elevationstart == None:
	el_start = int(args.elevationstart)
if not args.elevationend == None:
	el_end = int(args.elevationend)
if not args.frequency == None:
	user_freq = float(args.frequency)
if not args.biastee == None:
	bias_tee = int(args.biastee)
if not args.gain == None:
	user_gain = float(args.gain)
if not args.preview == None:
	preview_mode = int(args.preview)
#if not args.integration == None:
#	integration = int(args.integration)
if not args.bandwidth == None:
	bandwidth = float(args.bandwidth)


#generate timestamp
timestr = time.strftime('%Y%m%d-%H%M%S')

#Connect to Discovery Drive via its Wifi hotspot
dd_ip = '192.168.4.1' #default Discovery Drive IP when connected to onboard hotspot.
dd_port = 4533
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((dd_ip, dd_port))
client_socket.setblocking(1) #may not be necessary, this should be the default
	
print ('Connected to Discovery Drive on ', dd_ip)
print ('')

#Prompt for scan parameters, with default values and valid range checks
if args.azimuthstart is None: #if not already defined via argparse
	az_start = int(input('Starting Azimuth in degrees (0-360, default 90): ') or 90)
	if az_start < 0:
		print('Azimuth out of range, setting to 0')
		az_start = 0
	if az_start > 360:
		print('Azimuth out of range, setting to 360')
		az_start = 360
if args.azimuthend is None:
	az_end = int(input('Ending Azimuth in degrees (default 270): ') or 270)
	if az_end < 0:
		print('Azimuth out of range, setting to 0')
		az_end = 0
	if az_end > 360:
		print('Azimuth out of range, setting to 360')
		az_end = 360
az_end = az_end + 1 #ugly fix to get full user range inclusive
if args.elevationstart is None:
	el_start = int(input('Starting Elevation in degrees (0-90, default 30): ') or 30)
	if el_start < 0:
		print('Elevation out of range, setting to 0')
		el_start = 0
	if el_start > 90:
		print('Elevation out of range, setting to 90')
		el_start = 90
if args.elevationend is None:
	el_end = int(input('Ending Elevation in degrees (default 70): ') or 70)
	if el_end < 0:
		print('Elevation out of range, setting to 0')
		el_end = 0
	if el_end > 90:
		print('Elevation out of range, setting to 90')
		el_end = 90

az_start = az_start - 4 #scan a little extra to avoid offset issue
az_end = az_end + 4
	
#Configure SDR 
sdr = RtlSdr()
if args.frequency is None:
	user_freq = float(input('Frequency in MHz: '))
	if user_freq < 0.5:
		print('Frequency too low for RTL-SDR, setting to 500khz')
		user_freq = 0.5
	if user_freq > 1766:
		print('Frequency too high for RTL-SDR, setting to 1766')
		user_freq = 1766
if args.biastee is None:
	bias_tee = int(input('Bias Tee (1=on, 0=off, default 1): ') or 1)
	if bias_tee not in [0, 1]:
		print('Invalid Bias Tee value, setting to 0')
		bias_tee = 0
if args.gain is None:
	print ('Available gain values are ', sdr.valid_gains_db)
	print ('')
	user_gain = float(input('RF Gain (default 20.7, will be rounded to nearest available): ') or 20.7)
	if user_gain < 0:
		print('Gain below minimum for RTL-SDR, setting to 0')
		user_gain = 0
	if user_gain > 49.6:
		print('Gain above max for RTL-SDR, setting to 49.6')
		user_gain = 49.6
if args.preview is None:
	preview_mode = int(input('Preview results? (1=on, 0=off, default 1): ') or 1)
	if bias_tee not in [0, 1]:
		print('Invalid input, setting to 0')
		preview_mode = 0
#if args.integration is None:
#	integration = int(input('Integration time, example 256(fast), 1024(slow, default), etc') or 1024)
integration = 1024 #This works the best
if args.bandwidth is None:
	bandwidth = float(input('Bandwidth in kHz (default 8 / Narrow FM)' or 8))

sdr.sample_rate = 1e6 #MHz higher sample rates causing delays?
sdr.set_bandwidth(bandwidth*1000) 
sdr.center_freq = user_freq*1e6 # - 200e3 #MHz, with offset to avoid DC spike
sdr.gain = user_gain
sdr.set_bias_tee(bias_tee)

resolution = 1 #placeholder for potential future high-res scan, if can do fractional degrees of movement. 
np.savetxt(f"scan-settings-{timestr}.txt", (az_start,az_end,el_start,el_end,resolution,user_freq,bias_tee,user_gain))	


az_range = az_end - az_start + 1
el_range = el_end - el_start + 1



#Provide runtime estimate (Rough guess based on prior runs)
time_est = az_range * el_range
time_output = (time_est*1.2)/60
time_output = round(time_output, 2)
if time_output > 60:
	print(f'Estimated scan time with your parameters is {round(time_output/60, 2)} hours.\n')
else:
	print(f'Estimated scan time with your parameters is {time_output} minutes.\n')
user_confirm = input('Proceed with scan? (y/n):')
if user_confirm.lower().startswith("y"):
	print ('Scan in progress...')
else:
	print ('exiting.')
	exit()


#create 2D array for raw signal strengths
sky_data = np.zeros((el_range,az_range))

start_time = time.time()  # record start time of scan

# initialize starting dish position
print('Moving antenna to starting position...')

command = f"P {az_start} {el_start}".encode('ascii')
client_socket.send(command)
response = client_socket.recv(100)
print(f"Requesting move to {az_start}, {el_start}")#display requested starting position

#Wait for drive to reach starting position
while 1:
	command = ('p').encode('ascii')
	client_socket.send(command)
	response = client_socket.recv(100)
	actual_position = response.decode("utf-8").strip().split("\n")
	current_az = float(actual_position[0])
	current_el = float(actual_position[1])
	print(f"Current position: {actual_position[0]}, {actual_position[1]}")
	# Actual position might be +/- 1 of requested position
	if (az_start-1) <= round(current_az) <= (az_start+1) and (el_start-1) <= round(current_el) <= (el_start+1):
		break

#SDR always seems to be delayed by 1/10th of Az range, because reasons????
#Start reading from SDR "early" to avoid this. May not be the same on all machines.
for i in range (0, round((az_range)/10)+1): 
	samples = sdr.read_samples(256*1024) 	

#Spawn preview as separate process TODO: see if this affects performance
if preview_mode == 1:
	np.savetxt(f"raw-data-{timestr}.txt", sky_data)
	# call preview script with current data file
	subprocess.Popen(['python3', 'dd_preview.py', f"raw-data-{timestr}.txt"])


# Main scanning loop
direction = 1
for elevation in range(el_start, el_end+1):
	# avoid blank pixels at start(?)
	sdr_bytes = sdr.read_bytes(integration*1024)

	for azimuth in range(az_start, az_end):
		if (direction % 2) == 0:  # check for sweep direction
			# increment backwards on odd numbered loops
			azimuth = abs(azimuth-az_end)+az_start-1

		# Read RF signal from SDR
		# grab samples for averaging
		samples = sdr.read_samples(integration*1024)
		signal_strength = 10*log10(var(samples))
		print(f"Relative power: {round(signal_strength, 2)} dB")

		# record signal data to array
		sky_data[abs(elevation-el_end), (azimuth-az_end)] = signal_strength
		# write to text file
		np.savetxt(f"raw-data-{timestr}.txt", sky_data)

		# Tell drive to go to next target position
		command = f"P ' {azimuth} {elevation}".encode('ascii')
		client_socket.send(command)
		# response = client_socket.recv(100)
		# display current requested position
		print(f"Requesting move to Azimuth: {azimuth}, Elevation: {elevation}")

# 			#Wait for drive to reach next position before proceeding
#           #May want to keep this for Sandland version
#			while 1:
#				command = ('p').encode('ascii')
#				client_socket.send(command)
#				response = client_socket.recv(100)
#				actual_position = response.decode("utf-8").strip().split("\n")
#				current_az = float(actual_position[0])
#				current_el = float(actual_position[1])
#				print('Current position: ' + actual_position[0] + ', ' + actual_position[1])
#				#Actual position might be +/- 1 of requested position
#				if (azimuth-1) <= round(current_az) <= (azimuth+1) and (elevation-1) <= round(current_el) <= (elevation+1):
#					break

	direction = direction + 1  # change sweep direction for each elevation change

end_time = time.time()  # record end time of scan
print(f'\nScan complete! View results with: python3 dd_image.py raw-data-{timestr}.txt')
run_time = round(end_time - start_time)
print(f"Elapsed time: {round(run_time/60, 2)} minutes.")

#close connection and turn off SDR
client_socket.close()
sdr.set_bias_tee(0)
sdr.close()

