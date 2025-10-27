# This code is meant to store the URLs and IP addresses used in the Bucintoro project.
# If you are using a Novo Nordinsk machine, please uncomment the corresponding URLs and comment the default ones.
# Author: Sara Alemanno
# Date: 2025-10-20

import requests

URL_BACKEND = 'http://10.10.0.25'                           # Bucintoro Backend URL
URL_API = 'http://10.10.0.25/api/v2/main_status'            # API URL for REST requests
IP_PLC = '10.10.0.20'


#URL_BACKEND = 'http://10.10.150.99'                           # Bucintoro Backend URL
#URL_API = 'http://10.10.150.99/api/v2/main_status'            # API URL for REST requests
#IP_PLC = '10.10.150.20'

#NOVO NORDISK
#URL_API = 'http://172.30.135.41/api/v2/main_status'
#URL_BACKEND = 'http://172.30.135.41'

# === Fetch main status from Bucintoro API ===
# This function retrieves the main status from the Bucintoro API.
def get_main_status(URL_API):
    try:
        response = requests.get(URL_API)
        if response.status_code == 200:
            main_status = response.json()
            #print("Main status received:", data)
            return main_status
        else:
            print(f"Error fetching main status: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None