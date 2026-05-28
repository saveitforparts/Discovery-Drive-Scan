#Discovery Drive scan preview — Astronomy variant
#Companion file to dd_astron.py, shows live-updating results of long-integration scans
#10-minute timeout for astronomical scans (1420.4 MHz, Earth rotation compensation)
#Run as python3 dd_preview_a.py raw-data-<timestamp>.txt
#Kill this process with 'q'

def start(dataFile):
	from datetime import datetime, timedelta
	import numpy as np
	import matplotlib.pyplot as plt
	import keyboard
	import os

	print('Press \'q\' to exit preview mode (astronomy)')
	while True:
		try:
			with open(dataFile, 'r') as file_name:
				sky_data = np.loadtxt(file_name)

			sky_data[sky_data==0] = ['nan']

			header, *filename_parts = str(file_name).split('-')
			file_name = str(filename_parts[2])
			header, *split = file_name.split('.')
			timestamp = filename_parts[1] + '-' + header

			scan_params = np.loadtxt("scan-settings-" + timestamp + ".txt")
			az_start = int(scan_params[0])
			az_end = int(scan_params[1])
			el_start = int(scan_params[2])
			el_end = int(scan_params[3])
			resolution = int(scan_params[4])
			user_freq = str(round(scan_params[5], 2))
			bias_tee = int(scan_params[6])
			user_gain = str(scan_params[7])
			bias_str = "On" if bias_tee else "Off"

			cleaned_data = sky_data
			for row_index in range(el_end - el_start):
				if row_index % 2 == 0:
					cleaned_data[row_index] = np.roll(cleaned_data[row_index], -4)
				else:
					cleaned_data[row_index] = np.roll(cleaned_data[row_index], 3)

			cleaned_data = cleaned_data[:, 4:-4]
			az_end -= 1

			x = np.array([0, ((az_end-4)-(az_start+4))/2, az_end-az_start-7])
			az_range = np.array([az_start+4, ((az_start-4)+(az_end+4))/2, az_end-4])
			plt.xticks(x, az_range)
			y = np.array([0, (el_end-el_start)/2, el_end-el_start])
			el_range = np.array([el_end, (el_start+el_end)/2, el_start])
			plt.yticks(y, el_range)

			plt.imshow(cleaned_data, cmap='CMRmap')
			plt.colorbar(location='bottom', label='RF Signal Strength (dBm)')
			plt.xlabel("Azimuth")
			plt.ylabel("Elevation")
			plt.suptitle("Discovery Drive Scan " + timestamp)
			plt.title("Frequency: " + user_freq + "MHz, Gain: " + user_gain + ", Bias Tee: " + bias_str)

			#10-minute timeout for slow astronomical scans
			file_mod_time = datetime.fromtimestamp(os.stat(dataFile).st_mtime)
			now = datetime.today()
			max_delay = timedelta(minutes=10)

			if now - file_mod_time > max_delay:
				print(dataFile, "is no longer being updated. Close image window to quit.")
				plt.show(block=True)
				break

			plt.show(block=False)
			plt.pause(1)
			plt.clf()

			if keyboard.is_pressed("q"):
				plt.close("all")
				break

		except:
			print('Preview index mismatch, retrying...')
			continue
