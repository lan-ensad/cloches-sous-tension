from sol import Sol
from recorder import Recorder
from player import Player
from btn import BTN
import utils
import time
import asyncio
import mido
import RPi.GPIO as GPIO
import os
import datetime

##           LOAD CONFIG
config = utils.yaml_load_config('config.yaml')
## ====================================
##             CONFIG
PADS_NOTES = config['mapping']['pads']
MOT_PIN = config['mapping']['sol']
DRONY_NOTES = config['mapping']['drony_sol_notes']
POTAR_CONTROL = config['mapping']['potar_control']
drony_status = [False]*config['machine']['nb_motors']
NUMBER_DRAW = config['date']['total_draw']
## ====================================
##            TRIGGER DRAW
table = [[10, 50], [12, 50], [13, 50], [15, 50]] ## ACTIVATION TIME
index_auto_playing = 0
## ====================================
##          SWITCH AUTO/LIVE
btn = BTN(config['machine']['switch_btn_pin'], config['machine']['led_state_pin'])
## ====================================
##          MOTORS PIN TABLES
sol = []
for i in range(len(MOT_PIN)):
    sol.append(Sol(MOT_PIN[i]))
## ====================================
##            REC FUNCTIONS
score_dir = os.path.dirname(os.path.abspath(__file__))
rec = Recorder('score')
rec.score_ID = utils.how_many_scores(score_dir)+1
first_score = "score_"+str(config['date']['first_score'])+".txt"
pl = Player()
## ====================================
##         MAIN STATE AUTO/LIVE
listen_midi = None
midi_controller = None
playing_score = None
first_playing_score = True
midi_connected = False

async def connecting_controller(port_name):
    global midi_connected
    global midi_controller
    global listen_midi
    while True:
        try:
            midi_controller = mido.open_input(port_name)
            midi_connected = True
            print(f'connected {midi_controller}')
        except (IOError, OSError):
            print(f'{port_name} not found... Retry in 1scd')
        else:
            with midi_controller as midi_in:
                listen_midi = asyncio.create_task(handle_event(midi_in))
                await listen_midi
        await asyncio.sleep(1)

async def switch_state():
    global listen_midi
    global playing_score
    global first_playing_score
    global index_auto_playing
    global midi_controller
    while True:
        if btn.state:
            ##      LIVE MODE
            if btn.prev_state!=btn.state:
                if playing_score is not None:
                    playing_score.cancel()
                    playing_score = None
                    utils.reset_all_pwm()
                await connecting_controller(config['controller']['name'])
                # print('live')
                btn.prev_state = btn.state
        else:
            ##      READ SCORE
            if btn.prev_state!=btn.state:
                if listen_midi is not None:
                    listen_midi.cancel()
                    listen_midi = None
                    utils.reset_all_pwm()
                ##      BOOT READ SCORE
                if first_playing_score:
                    print('first playing...')
                    time.sleep(180) # Wait before play the first score
                    playing_score = asyncio.create_task(handle_score("score_25.txt"))
                if not first_playing_score:
                    playing_score = asyncio.create_task(handle_score("score_25.txt"))
                btn.prev_state = btn.state
        await asyncio.sleep(0.01)

async def handle_score(sc: str):
    global first_playing_score
    global index_auto_playing
    played = False
    pl.read_file(sc)
    while True:
        if first_playing_score:
            for item in pl.raws:
                if item.isdigit():
                    delay = int(item)
                    await asyncio.sleep(delay/1000)
                else:
                    message = pl.parse_midi_string(item)
                    ### ===================================================
                    ###                     NOTE_ON
                    if message.type == "note_on":
                        ###   DRONYING
                        if message.note in DRONY_NOTES:
                            index = DRONY_NOTES.index(message.note)
                            if not sol[index].dronying: ## prevent axe shifting when dronying
                                await sol[index].toggle_drone(utils.convert(message.velocity), 250)
                                drony_status[index] = True
                                print(f'Activate sol drony {DRONY_NOTES.index(message.note)+1}')
                        ###   ONT TAPE 
                        if message.note in PADS_NOTES :
                            index = PADS_NOTES.index(message.note)
                            if not drony_status[index]:
                                await sol[index].tape(utils.convert(message.velocity))
                                print(f'cloche n°{PADS_NOTES.index(message.note)+1} at {message.velocity} travel time: {sol[PADS_NOTES.index(message.note)].hit_length}')
                    ### ===================================================
                    ###                     NOTE_OFF
                    if message.type == "note_off":
                        if message.note in DRONY_NOTES:
                            index = DRONY_NOTES.index(message.note)
                            await sol[index].toggle_drone()
                            drony_status[index] = False
                            print(f'Deactivate sol drony {DRONY_NOTES.index(message.note)+1}')
                    ### ===================================================
                    ###                 CONTROL CHANGE
                    if message.type=="control_change":
                        if message.control in POTAR_CONTROL:
                            index = POTAR_CONTROL.index(message.control)
                            if drony_status[index]:
                                sol[index].stream_potar(utils.map_val(message.value, 0, config['signal']['input_max'], config['signal']['drony_min'], config['signal']['drony_max']))
            first_playing_score = False
            utils.reset_all_pwm()
        else:
            utils.reset_all_pwm()
            now = [datetime.datetime.now().hour, datetime.datetime.now().minute]
            target = table[index_auto_playing]
            print(f'Waiting next alignement | now:{now}\ttarget:{target}')
            if now[0]>target[0]:
                index_auto_playing +=1
                print('index +1')
            elif now[0]==target[0] and now[1]>target[1]:
                index_auto_playing +=1
                print('index +1')
            elif now == target:
                if not played :
                    for item in pl.raws:
                        if item.isdigit():
                            delay = int(item)
                            await asyncio.sleep(delay/1000000)
                        else:
                            message = pl.parse_midi_string(item)
                            # print(message)
                            ### ===================================================
                            ###                     NOTE_ON
                            if message.type == "note_on":
                                ###   DRONYING
                                if message.note in DRONY_NOTES:
                                    index = DRONY_NOTES.index(message.note)
                                    if not sol[index].dronying: ## prevent axe shifting when dronying
                                        await sol[index].toggle_drone(utils.convert(message.velocity), 250)
                                        drony_status[index] = True
                                        print(f'Activate sol drony {DRONY_NOTES.index(message.note)+1}')
                                ###   ONT TAPE 
                                if message.note in PADS_NOTES :
                                    index = PADS_NOTES.index(message.note)
                                    if not drony_status[index]:
                                        await sol[index].tape(utils.convert(message.velocity))
                                        print(f'cloche n°{PADS_NOTES.index(message.note)+1} at {message.velocity} travel time: {sol[PADS_NOTES.index(message.note)].hit_length}')
                            ### ===================================================
                            ###                     NOTE_OFF
                            if message.type == "note_off":
                                if message.note in DRONY_NOTES:
                                    index = DRONY_NOTES.index(message.note)
                                    await sol[index].toggle_drone()
                                    drony_status[index] = False
                                    print(f'Deactivate sol drony {DRONY_NOTES.index(message.note)+1}')
                            ### ===================================================
                            ###                 CONTROL CHANGE
                            if message.type=="control_change":
                                if message.control in POTAR_CONTROL:
                                    index = POTAR_CONTROL.index(message.control)
                                    if drony_status[index]:
                                        sol[index].stream_potar(utils.map_val(message.value, 0, config['signal']['input_max'], config['signal']['drony_min'], config['signal']['drony_max']))
                ### ===================================================
                ###                 AFTER PLAYED SCORE
                index_auto_playing+=1 ## wait the next trigger time
                utils.reset_all_pwm()
        await asyncio.sleep(1) ## Testing alignement every 1 scd

async def handle_event(midi_in):
    while True:
        message = midi_in.poll()
        if message:
            # print(str(message))
            if message.type != 'sysex':
                rec.record_score(str(message))
            ### ===================================================
            ###                 CONTROL CHANGE
            if message.type == 'control_change':
                ###   RECORD CONTROL
                if message.control == config['mapping']['rec']:
                    if message.value == config['signal']['input_max'] :
                        rec.record_status = True
                    else :
                        rec.record_status = False
                        rec.score_ID +=1
                if message.control in POTAR_CONTROL:
                    index = POTAR_CONTROL.index(message.control)
                    if drony_status[index]:
                        sol[index].stream_potar(utils.map_val(message.value, 0, config['signal']['input_max'], config['signal']['drony_min'], config['signal']['drony_max']))
            ### ===================================================
            ###                     NOTE_OFF
            if message.type == 'note_off':
                if message.note in DRONY_NOTES:
                    index = DRONY_NOTES.index(message.note)
                    await sol[index].toggle_drone()
                    drony_status[index] = False
                    print(f'Deactivate sol drony {DRONY_NOTES.index(message.note)+1}')
            ### ===================================================
            ###                     NOTE_ON
            if message.type == 'note_on':
                ###   DRONYING
                if message.note in DRONY_NOTES:
                    index = DRONY_NOTES.index(message.note)
                    if not sol[index].dronying: ## prevent axe shifting when dronying
                        await sol[index].toggle_drone(utils.convert(message.velocity), config['signal']['drony_start'])
                        drony_status[index] = True
                        print(f'Activate sol drony {DRONY_NOTES.index(message.note)+1}')
                ###   ON TAPE 
                if message.note in PADS_NOTES :
                    index = PADS_NOTES.index(message.note)
                    if not drony_status[index]:
                        await sol[index].tape(utils.convert(message.velocity))
                        print(f'cloche n°{PADS_NOTES.index(message.note)+1} at {message.velocity} travel time: {sol[PADS_NOTES.index(message.note)].hit_length}')
            ## ===================================================
        await asyncio.sleep(0.000001)

async def main():
    utils.reset_all_pwm()
    listen_btn = asyncio.create_task(btn.read_state())
    listen_switch = asyncio.create_task(switch_state())
    await listen_btn
    await listen_switch

asyncio.run(main())