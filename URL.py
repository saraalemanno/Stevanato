import requests

URL_BACKEND = 'http://10.10.0.25'                           # Bucintoro Backend URL
URL_API = 'http://10.10.0.25/api/v2/main_status'            # API URL for REST requests

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