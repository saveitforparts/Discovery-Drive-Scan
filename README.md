# Discovery Drive sky scan script

Microwave imaging using Discovery Drive from KrakenRF. 

Gabe Emerson / Saveitforparts 2026. Email: gabe@saveitforparts.com

Video demo:

![Discovery Drive with Discovery Dish](https://github.com/saveitforparts/Discovery-Drive-Scan/blob/main/images/discovery%20drive.png)

**Introduction:**

This code controls a commercial azimuth/elevation rotor over TCP. It is designed for the KrakenRF
Discovery Drive, but should work for other generic rotors that use the rotctld / hamlilb standard.
(Some connection details like IP Address are hard-coded assuming a Discovery Drive, and will need
to be changed if you use another rotor). 

The dd_scan.py script steps the drive through a specified azimuth/elevation range and records
signal strength at each position. The accompanying dd_image.py script creates a heatmap from
the collected data. The dd_preview.py script is similar to dd_image and creates a live-updating
preview of the data as it's collected. It is optional and can be run separately during a scan, or
called from dd_scan by flagging the preview option on, Frequencies are depended on a user-supplied
antenna and feed. I used the Discovery Dish and various feeds, you could also us a Yagi-Uda antenna
like the Arrow II, or a different directional antenna for other frequencies. 

**Requirements:**

dd_scan uses socket, sys, time, regex, numpy, pyrtlsdr, pylab, argparse, and subprocess. 
dd_image uses matplotlib. dd_preview uses os and keyboard (keyboard requires running as root). 

Any missing dependencies can be installed by running "pip install -r requirements.txt"

**Setup and use**

Connect to the Discovery Drive's onboard Wifi hotspot, the default IP of the drive should be
192.168.4.1 (If this has changed you'll need to edit dd_scan with the new IP). Connect your antenna,
feed, and RTL-SDR. Run the scan with "python3 dd_scan.py", optionally you can add arguments from 
the terminal. If no arguments are passed, or if only some arguments are passed, the script will
prompt you for the remaining scan parameters. In either case you will be told the estimated run 
time and asked if you want to continue (y/n). 

Parameters are:
- -as Azimuth start, the beginning of the azimuth range. 
- -ae Azimuth end, the end of the azimuth range
- -es Elevation start
- -ee Elevation end
- -f Frequency of the scan
- -bt Bias Tee enabled (1) or disabled (0)
- -g Gain for RTL-SDR
- -p Preview mode enabled (1) or disabled (0)
- -i Integration time. Shorter should result in a faster scan but possibly less smooth data.
- -bw Bandwidth of the scan in kHz. 8 is equivalent to Narrow FM, 250 is close to Wideband FM, etc. 

The script will generate two files while it runs. The first is scan-settings-<timestamp>.txt which
records the scan parameters. The second is raw-data-<timestamp>.txt which holds the numpy array of
signal strength values. Both files are needed to produce a heatmap image with dd_image.py

If you have selected the preview mode via command-line argument or prompt, the dd_preview.py script
will launch as a subprocess once the dish begins scanning. It will fill in the data as it's received
from the RTL-SDR. The script re-caluclates a normal spread each time, so the color scheme of the 
heatmap will change as new upper or lower values come in. You can also run this code separately against
a currently active raw-data file. dd_preview can be cancelled with 'q' (may need to hold down q). 
It will stop updating when the raw-data file is full, and closing the image window at that point will
end the script. 

Please note that dd_preview (either run directly or called from dd_scan) requires root priveledges. 

After the scan is finished, if you didn't use the preview mode, you can create a heatmap from the 
data by running "python3 dd_image.py raw-data-<timestamp>.txt"

**Examples**

Parameters used to scan both GOES-E and GOES-W from Minnesota:

"python3 dd_scan.py -as 140 -ae 250 -es 15 -ee 45 -bt 1 -f 1694.1 -g 20 -p 1 -1 1024 -bw 8"

The resulting heatmap is below, showing GOES-19 in the E orbital slot on the left and GOES-18 
in the W orbital slot on the right. 

![Example GOES scan](https://github.com/saveitforparts/Discovery-Drive-Scan/blob/main/images/GOES.png)

**Notes**

The Discovery Dish has a wide beamwidth, so you may get larger signal "blobs" in the heatmaps. Other 
antennas could result in a more focused scan with smaller signal areas. Larger scan ranges can give
a better overall picture of the sky, but will take longer to complete. 

Medium-Earth-Orbit satellites like GPS, Glonass, Beidou, etc can be imaged with smaller scan ranges
and/or faster speeds, but may show up as elongated blobs due to motion during the scan. Note that
some geostationary satellite transmit on GPS L1 for WAAS so may also appear in a scan of GPS
frequencies alongside the MEO satellites. 





