from sol import Sol
from player import Player
import utils
import time
import board
import asyncio
import RPi.GPIO as GPIO

##           LOAD CONFIG
config = utils.yaml_load_config('config.yaml')
## ====================================
##             CONFIG
PADS_NOTES = config['mapping']['pads']
MOT_PIN = config['mapping']['sol']
DRONY_NOTES = config['mapping']['drony_sol_notes']
POTAR_CONTROL = config['mapping']['potar_control']
## ====================================
##          SWITCH AUTO/LIVE
btn_pin = config['machine']['switch_btn_pin']
led_pin = config['machine']['led_state_pin']
led = GPIO.setup(led_pin, GPIO.OUT)
btn = GPIO.setup(btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
btn_state = 0
## ====================================
##          MOTORS PIN TABLES
sol = []
for i in range(len(MOT_PIN)):
    sol.append(Sol(MOT_PIN[i]))

pl = Player()

async def play():
    pl.read_file('score_1.txt')
    for i in range(len(pl.raw)):
        delay = pl.parse_line(i)['delay']
        ## =====================================
        ##              NOTES
        if pl.parse_line(i)['note']:
            note = pl.parse_line(i)['note']
            if pl.parse_line(i)['velocity']:
                velocity = pl.parse_line(i)['velocity']
            ## DRONYING
            if note in DRONY_NOTES:
                index = DRONY_NOTES.index(pl.parse_line(i)['note'])
                await sol[index].toggle_drone(utils.convert(velocity), 500)
            ##  ONE TAPE
            if note in PADS_NOTES:
                index = PADS_NOTES.index(pl.parse_line(i)['note'])
                await sol[index].tape(utils.convert(velocity))
        ## =====================================
        ##              CONTROL
        if pl.parse_line(i)['control_change']:
            value = pl.parse_line(i)['velocity']
            index = POTAR_CONTROL.index(pl.parse_line(i)['control_change'])
            sol[index].stream_potar(utils.map_val(value, 0, 127, 250, 5000))
        await asyncio.sleep(delay/1000)

async def main():
    await play()

asyncio.run(main())