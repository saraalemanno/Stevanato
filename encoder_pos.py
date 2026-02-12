# This code is meant to keep track of the position of the encoder
# and make it available for other scripts to be synced with it.
from ArduinoController import get_pos_encoder
pos_encoder = 0

'''def update_position(impulse_count):
    global pos_encoder
    pos_encoder = (impulse_count * 4) % 400         # 400 pulses per revolution'''

def get_position():
    return pos_encoder