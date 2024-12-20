import time
import asyncio
import mido
import yaml
import busio
import board
from adafruit_pca9685 import PCA9685
from typing import List, Dict, Any
from pathlib import Path
import os
import random
import datetime

def reset_all_pwm():
    for e in range(16):
        pca.channels[e].duty_cycle = 0
    print('reset all pwm ok')

def yaml_load_config(filename: str)-> Dict[str, Any]:
    conf = yaml.safe_load(Path(filename).read_text())
    return conf

## ====================================
##             CONFIG
config = yaml_load_config('config.yaml')
INPUTMAX = config['signal']['input_max']
OUTPUTMAX = config['signal']['output_max']
INPUTMIN = config['signal']['input_min']
OUTPUTMIN = config['signal']['output_min']
## ====================================
##              PCA9685
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c, reference_clock_speed=config['PWM']['clock'])
pca.frequency = config['PWM']['freq']
## ====================================
midi_connected = False

## ==========================================
##  DRAW RANDOM HOURS AND MINUTE TO ACTIVATE
def draw_lottery():
    hour = random.randint(config['date']['hour_range'][0],config['date']['hour_range'][1])
    if hour <= datetime.datetime.now().hour:
        delta = datetime.datetime.now().hour - hour
        hour += delta+1
    minute = random.randint(config['date']['minute_range'][0],config['date']['minute_range'][1])
    ttime = [hour, minute]
    return ttime

def many_draw(h_many: int):
    ttime = []
    for i in range(h_many):
        ttime.append(draw_lottery())
    return sorted(ttime, key=lambda x: (x[0], x[1]))
## ==========================================

def pwm_write(channel, power):
    """write duty_cycle (power) in the channel of the pca object"""
    pca.channels[channel].duty_cycle = power

def find_index(list, val):
    """find the nearest index of val in the list"""
    nearest_index = min(range(len(list)), key=lambda i: abs(list[i] - val))
    return nearest_index

def available_ports():
    """return availables ports"""
    ports = mido.get_input_names()
    return ports

def rand_scores(score_dir):
    """Chose random score in the folder"""
    scores = [f for f in os.listdir(score_dir) if f.endswith('.txt')]
    draw = random.randint(0, len(scores))
    return scores[draw-1]

def how_many_scores(score_dir):
    """Return the number of .txt format in the root folder"""
    scores = [f for f in os.listdir(score_dir) if f.endswith('.txt')]
    return len(scores)

async def connecting_controller(port_name):
    global midi_connected
    while not midi_connected:
        try:
            midi_controller = mido.open_input(port_name)
            print(f'connected')
            return midi_controller
        except (IOError, OSError):
            print(f'{port_name} not found... Retry in 1scd')
    await asyncio.sleep(1)

def map_val(x, inm, inM, oum, ouM):
    """map a range to another"""
    return max(min(ouM, (x - inm) * (ouM - oum) // (inM - inm) + oum), oum)

def convert(x):
    """function that map 6bits to 16bits value"""
    return max(min(OUTPUTMAX, (x - INPUTMIN) * (OUTPUTMAX - OUTPUTMIN) // (INPUTMAX - INPUTMIN) + OUTPUTMIN), OUTPUTMIN)