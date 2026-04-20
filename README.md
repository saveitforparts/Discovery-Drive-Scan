#Discovery Drive sky scan script

Microwave imaging using Discovery Drive from KrakenRF. 

Gabe Emerson / Saveitforparts 2026. Email: gabe@saveitforparts.com
Video demo:

Introduction:

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

Requirements:

dd_scan uses socket, sys, time, regex, numpy, rtlsd, pylab, argparse, and subprocess. 
dd_image uses matplotlib. dd_preview uses os and keyboard (keyboard requires running as root). 

Any missing dependencies can be installed by running "pip install -r requirements.txt"

dd_


dd_scan: does the scan
dd_image: creates an image from a raw_data file
dd_preview: shows a live-updating preview of the scan data

To use dd_preview run it from a separate terminal window against the current raw_data file while dd_scan is active.
As the file is updated by the active dd_scan, dd_preview will show the new data
dd_preview can be cancelled with 'q' (may need to hold down q). Or it will stop when the raw_data file is full. 
dd_preview needs to be run as root
