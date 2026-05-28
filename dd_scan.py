#Python program to scan with Discovery Drive and output signal strength array
#Process output into bitmap with dd_image.py
#Version 1.1
#Gabe Emerson / Saveitforparts 2026, Email: gabe@saveitforparts.com

import socket, time, argparse
from rtlsdr import RtlSdr
import numpy as np

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

parser.add_argument("-ip", "--ip", help="The lan IP address to connect to. (defaults to 192.168.4.1)")
parser.add_argument("-po", "--port", help="The port of the lan dish you want to connect to. (defaults to 4533)")
args = parser.parse_args()


# Ensure settings
az_start = int(args.azimuthstart) if args.azimuthstart is not None else None
az_end = int(args.azimuthend) if args.azimuthend is not None else None
el_start = int(args.elevationstart) if args.elevationstart is not None else None
el_end = int(args.elevationend) if args.elevationend is not None else None
user_freq = float(args.frequency) if args.frequency is not None else None
bias_tee = int(args.biastee) if args.biastee is not None else None
user_gain = float(args.gain) if args.gain is not None else None
preview_mode = args.preview == '1' if args.preview is not None else None
bandwidth = float(args.bandwidth) if args.bandwidth is not None else None
dd_ip = args.ip if args.ip is not None else '192.168.4.1'
dd_port = int(args.port) if args.port is not None else 4533

#generate timestamp
timestr = time.strftime('%Y%m%d-%H%M%S')

#Connect to Discovery Drive via its Wifi hotspot
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((dd_ip, dd_port))
client_socket.setblocking(1) #may not be necessary, this should be the default

print('Connected to Discovery Drive on ', dd_ip)

def clamp(val, lo, hi, name):
	if val < lo: print(f'{name} out of range, setting to {lo}'); return lo
	if val > hi: print(f'{name} out of range, setting to {hi}'); return hi
	return val

def ask(prompt, cast, default=None, lo=None, hi=None, name='', allowed=None):
	raw = input(prompt)
	if not raw and default is not None:
		return default
	val = cast(raw)
	if lo is not None or hi is not None:
		val = clamp(val, lo, hi, name)
	if allowed is not None and val not in allowed:
		print(f'Invalid {name} value, setting to {allowed[0]}')
		val = allowed[0]
	return val

#Prompt for scan parameters, with default values and valid range checks
if args.azimuthstart is None:
	az_start = ask('Starting Azimuth in degrees (0-360, default 90): ', int, 90, 0, 360, 'Azimuth')

if args.azimuthend is None:
	az_end = ask('Ending Azimuth in degrees (default 270): ', int, 270, 0, 360, 'Azimuth')

if args.elevationstart is None:
	el_start = ask('Starting Elevation in degrees (0-90, default 30): ', int, 30, 0, 90, 'Elevation')

if args.elevationend is None:
	el_end = ask('Ending Elevation in degrees (default 70): ', int, 70, 0, 90, 'Elevation')

az_start -= 4
az_end += 5
sdr = RtlSdr()

if args.frequency is None: user_freq = ask('Frequency in MHz: ', float, None, 0.5, 1766, 'Frequency')
if args.biastee is None:    bias_tee = ask('Bias Tee (1=on, 0=off, default 1): ', int, 1, allowed=(0, 1), name='Bias Tee')
if args.preview is None:preview_mode = bool(ask('Preview results? (1=on, 0=off, default 1): ', int, 1, allowed=(0, 1), name='Preview'))
if args.gain is None:
	print('Available gain values are ', sdr.valid_gains_db, '\n')
	user_gain = ask('RF Gain (default 20.7, will be rounded to nearest available): ', float, 20.7, 0, 49.6, 'Gain')

#if args.integration is None:
#	integration = int(input('Integration time, example 256(fast), 1024(slow, default), etc') or 1024)

integration = 1024 #This works the best
if args.bandwidth is None:
	bandwidth = ask('Bandwidth in kHz (default 8 / Narrow FM): ', float, 8)

sdr.sample_rate = 1e6 #MHz higher sample rates causing delays?
sdr.set_bandwidth(bandwidth*1000) 
sdr.center_freq = user_freq*1e6 # - 200e3 #MHz, with offset to avoid DC spike
sdr.gain = user_gain
sdr.set_bias_tee(bias_tee)

resolution = 1 #placeholder for potential future high-res scan, if can do fractional degrees of movement. 
np.savetxt('scan-settings-' + timestr +'.txt', (az_start,az_end,el_start,el_end,resolution,user_freq,bias_tee,user_gain))	

az_range = az_end - az_start + 1
el_range = el_end - el_start + 1

#Provide runtime estimate (Rough guess based on prior runs)
time_est = az_range * el_range
time_output = (time_est*1.2)/60
time_output = round(time_output, 2)

if time_output > 60: print('Estimated scan time with your parameters is ', round(time_output/60, 2), ' hours.\n')
else:                print('Estimated scan time with your parameters is ', time_output, ' minutes.\n')

user_confirm = input('Proceed with scan? (y/n):')

if user_confirm.lower().startswith("y"): print('Scan in progress...')
else:                                    print('Exiting.'); exit()

#create 2D array for raw signal strengths
sky_data = np.zeros((el_range,az_range))

start_time = time.time() #record start time of scan
#initialize starting dish position
print('::: Moving antenna to starting position...\n')
command = ('P ' + str(az_start) + ' ' + str(el_start)).encode('ascii')
client_socket.send(command)
response = client_socket.recv(100)
print('-> Requesting move to ', az_start, ', ', el_start)  #display requested starting position

#Wait for drive to reach starting position
while True:
	command = ('p').encode('ascii')
	client_socket.send(command)
	response = client_socket.recv(100)
	actual_position = response.decode("utf-8").strip().split("\n")
	current_az = float(actual_position[0])
	current_el = float(actual_position[1])
	print('-> Current position: ' + actual_position[0] + ', ' + actual_position[1])
	#Actual position might be +/- 1 of requested position
	if abs(round(current_az) - az_start) <= 1 and abs(round(current_el) - el_start) <= 1: break

#SDR always seems to be delayed by 1/10th of Az range, because reasons????
#Start reading from SDR "early" to avoid this. May not be the same on all machines.
for i in range (0, round((az_range)/10)+1): 
	samples = sdr.read_samples(256*1024)

#Spawn preview as separate process TODO: see if this affects performance

if preview_mode:
	np.savetxt(f"raw-data-{timestr}.txt", sky_data)

	#call preview script with current data file
	import dd_preview
	dd_preview.start(f'raw-data-{timestr}.txt')

	#subprocess.Popen(['python3', 'dd_preview.py', 'raw-data-' + timestr +'.txt']) 

#Main scanning loop
direction=1
for elevation in range (el_start,el_end+1):
	sdr_bytes = sdr.read_bytes(integration*1024) #avoid blank pixels at start(?)
	for azimuth in range (az_start,az_end):
		if (direction % 2) == 0: #check for sweep direction
			azimuth = abs(azimuth-az_end)+az_start-1 #increment backwards on odd numbered loops						#Read RF signal from SDR
		samples = sdr.read_samples(integration*1024) #grab samples for averaging 
		signal_strength = 10*np.log10(np.var(samples))
		print('Relative power: ', round(signal_strength, 2),'dB') 
		
		#record signal data to array
		sky_data[abs(elevation-el_end),(azimuth-az_end)]=signal_strength
		#write to text file
		np.savetxt(f"raw-data-" + timestr +".txt", sky_data)
			
		#Tell drive to go to next target position
		command = ('P ' + str(azimuth) + ' ' + str(elevation)).encode('ascii')
		client_socket.send(command)
		#response = client_socket.recv(100)
		print('Requesting move to Azimuth: ', azimuth, ', Elevation: ', elevation)  #display current requested position
			
		# #Wait for drive to reach next position before proceeding
		# #May want to keep this for Sandland version
		# while True:
		# 	command = ('p').encode('ascii')
		# 	client_socket.send(command)
		# 	response = client_socket.recv(100)
		# 	actual_position = response.decode("utf-8").strip().split("\n")
		# 	current_az = float(actual_position[0])
		# 	current_el = float(actual_position[1])
		# 	print('Current position: ' + actual_position[0] + ', ' + actual_position[1])
		# 	#Actual position might be +/- 1 of requested position
		# 	if abs(round(current_az) - azimuth) <= 1 and abs(round(current_el) - elevation) <= 1:
		# 		break

		direction += 1	#change sweep direction for each elevation change

end_time = time.time() #record end time of scan
print('\nScan complete! View results with: python3 dd_image.py raw-data-' + timestr +'.txt')
print('Elapsed time: ', round((end_time - start_time) / 60, 2), ' minutes.')      

#close connection and turn off SDR
client_socket.close()
sdr.set_bias_tee(0)
sdr.close()