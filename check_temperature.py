# This code is meant to check the intern temperature of the device and stop the test if the temperature is too high
# The critical temperature is set to 60 degrees Celsius
# The normal operating temperature is between 30 and 45 degrees Celsius
# The temperature is fetched from the Bucintoro API by requesting the main status, every 10 seconds
# Author: Sara Alemanno
# Date: 2025-10-09
# Version: 0

import requests
import time
import threading
import sys
from URL import get_main_status

#URL_API = 'http://10.10.0.25/api/v2/main_status'              # API URL for REST requests
#stop_test = False
critical_temperature = 60                                     # Critical temperature in degrees Celsius
stop_event = threading.Event()
    
# === Monitor the temperature of the device ===

def monitor_temperature(URL_API, stop_event):
    while not stop_event.is_set():
        '''if pause_event.is_set():
            time.sleep(1)
            print("[BOTH] DEBUG")
            continue  # Skip the rest of the loop if paused'''
        
        main_status = get_main_status(URL_API)
        if main_status is None:
            continue  # If failed to retrieve main status, skip this iteration and try again
        
        # Extract the temperature value from the main status
        temperature = main_status.get('temperature', None)
        if temperature is None:
            continue  # If temperature data is not found, skip this iteration and try again
        
        print(f"[LOG][TEMP] Current Temperature: {temperature} °C")
        
        if temperature >= critical_temperature:
            print(f"[BOTH][TEMP]\033[1m\033[91mCRITICAL\033[0m: Temperature {temperature} °C exceeds critical limit of {critical_temperature} °C! Stopping the test.")
            stop_event.set()
            #break
        
        time.sleep(10)  # Check temperature every 10 seconds

    