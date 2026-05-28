#Discovery Drive scan preview
#Companion file to dd_scan.py, shows live-updating results of scan
#Run this from a separate terminal (as root) after dd_scan has started and raw_data file has been created
#Run as python3 dd_preview raw_data... (use active raw data file)
#Pyplot window will live update with latest scan results
#Kill this process with 'q'

def start(dataFile): # Cleaner entrypoint - so you dont have to rely on Popen & sys
	from datetime import datetime, timedelta
	import numpy as np
	import matplotlib.pyplot as plt
	import keyboard
	import os

	print('Press \'q\' to exit preview mode')
	while True:
		try:
			#Open the filename passed at runtime
			with open(dataFile, 'r') as file_name:
				sky_data = np.loadtxt(file_name)

			sky_data[sky_data==0]=['nan'] #convert 0s to NaN for visualization range
		
			#Pull timestamp from filename (there's probably a better way to do this)
			header, *filename_parts = str(file_name).split('-')     
			file_name=str(filename_parts[2])
			header, *split = file_name.split('.')
			timestamp=(filename_parts[1]+'-'+header)

			scan_params = np.loadtxt("scan-settings-"+timestamp+".txt")
			az_start=int(scan_params[0])
			az_end=int(scan_params[1])
			el_start=int(scan_params[2])
			el_end=int(scan_params[3])
			resolution=int(scan_params[4])
			user_freq=str(round(scan_params[5], 2))
			bias_tee=int(scan_params[6])
			user_gain=str(scan_params[7])

			if bias_tee==1: bias_str="On"
			else:           bias_str="Off"

			cleaned_data = sky_data
			#deal with indexing offset problem
			for row_index in range(0,(el_end-el_start)): #iterate through array
				if (row_index %2) == 0: #check for scan direction
					cleaned_data[row_index]=np.roll(cleaned_data[row_index],-4) #shift odd rows right 4 pixels
				else:
					cleaned_data[row_index]=np.roll(cleaned_data[row_index],3) #shift even rows left 3 pixels
			
			cleaned_data = cleaned_data[:, 4:-4]
			az_end -= 1

			#set up custom axis labels
			x=np.array([0,((az_end-4)-(az_start+4))/2,az_end-az_start-7])
			az_range=np.array([az_start+4,((az_start-4)+(az_end+4))/2,az_end-4])
			plt.xticks(x,az_range)
			y=np.array([0,(el_end-el_start)/2,el_end-el_start])
			el_range=np.array([el_end,(el_start+el_end)/2,el_start])
			plt.yticks(y,el_range)

			plt.imshow(cleaned_data, cmap='CMRmap')
			plt.colorbar(location='bottom',label='RF Signal Strength (dBm)')
			plt.xlabel("Azimuth")
			plt.ylabel("Elevation")
			plt.suptitle("Discovery Drive Scan "+timestamp)
			plt.title("Frequency: " + user_freq +"MHz, Gain: " + user_gain + ", Bias Tee: "+ bias_str) 

			#close preview if file is no longer being written
			file_mod_time = datetime.fromtimestamp(os.stat(dataFile).st_mtime) #when was file modified
			now = datetime.today() #when is current time
			max_delay = timedelta(seconds=5)

			if now-file_mod_time > max_delay:
				print(dataFile, "is no longer being updated. Close image window to quit.")
				plt.show(block=True)
				break

			#refresh image plot in infinite loop
			#animation would be better, but I don't understand how to use it
			plt.show(block=False)
			plt.pause(1) #pause for 1 second before updating
			plt.clf()  #clear and re-use existing figure window

			if keyboard.is_pressed("q"):  #user escape option
				plt.close("all")
				break

		except: #sometimes the array size changes and crashes things (why?)
			print('Preview index mismatch, retrying...')
			continue