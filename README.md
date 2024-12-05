# cloches sous tensions

- [How it works](#how-it-works)
    - [hardware diagram](#hardware-diagram)
    - [Software diagram](#software-diagram)
- [Usage](#usage)
    - [Two modes](#two-modes)
    - [config.yaml](#configyaml)
    - [Class & Functions](#class--functions)
- [hardware limitations](#hardware-limitations)
<!-- /TOC -->


This project was born in collab with [Francois Dufeil](https://francoisdufeil.com/) and his sculptural works. 

[IMAGE]

It uses a raspberry PCA9685 shield and 16 solenoides ITS-LS3830BD.

Python script runs `@reboot`

## How it works

### hardware diagram

![hardware](diagram_hardware.svg)

### Software diagram


## Usage

### Two modes

- live 
    - activate solenoides with a midi crontoller
    - in `config.yaml` you can sets :
        - `message.note` sets:`config.yaml ['mapping']['pads']`\
            to map the midi note of the controller
        - `message.velocity` sets:`config.yaml['signal']` \
            it use the velocity to trigg the mosfet
        - record a score. Note that the score is not recorded in .midi but in .txt (cf.[Class & Functions](#class--functions)>recorder)
        - `message.control_change` to active dronying sets:`config.yaml ['mapping']['drony_sol_notes']`
            - tick the `message.velocity` in the activation
        - control change to modify the delay time for the drony sets:`config.yaml ['mapping']['potar_control']`
    - remind to set the mapping before
    - for the happening we use: 
        - Arturia KeyStep Pro → MIDI out
        - MIDI in → Arturia BeatStep Pro
    - do not care about `message.channel` or `message.time`
- auto
    - read a score recorded
    - in `config.yaml` `date` where can set the range and the number of `draw_lottery()` defines in `utils.py`
    - when auto mode is triggered, `handle_score()` will read at once a score. After the `first_playing_score` is set to False and the function wait to align now() to the target() to read another score
    - `table_draw` is define with the `utils.many_draw(x)` function where x is the number of auto will be triggered

### config.yaml

### Class & Functions

- sol\
It's base on async to let the motor the time to reach the contact point with the bells. 
    - `tape()`\
    It automaticly set the travel_time `self.hit_length` by searching in the config.yaml at machine->motors->travel_time
    - `toggle_drony()`\
    When call, it create an async task `self.drony()` or cancels it if `self.dronying` is True. It free some bandwith for the midi signal and you can set the time between two tapes with the `midi.control_change.value` into the `stream_potard()`
    - `drony()`\
    Do not call by itself. The security heat setting is comments, ad the frequency calculator. the `self.delai_off` is set with the `self.stream_potar()` function
    - `get_timer()`\
    It uses by security settings as well as frequency calculator

- recorder
    - `get_current_millis()`\
    the recorder needs to know the duration between two midi note. Yes it's only 1ms definition >.<
    - `write()` and `record()`\
    realy simple and automated. You can call the `rec.record_score()` in each loop, it will record as the `rec.record_status == True` and stop when is False.

You can take a look at the `handle_score()` in `main.py` or `recorder.py`.

This is a sample of recorder looks like :
```
450
note_on channel=0 note=67 velocity=40 time=0
106
note_off channel=0 note=67 velocity=64 time=0
387
note_on channel=0 note=68 velocity=100 time=0
```
- player
    - `read_file()`\
    load a score in `self.raws`
    - `parse_midi_string`\
    use the mido `Message()` function to return the line's score into a midi message

The `handle_score()` in `main.py` parse the file line by line to consider odds line with the delay between to midi messages.

## hardware limitations

- Because MIDI send 7bits values and the PCA9685 use 16bits value, consider use the `utils.convert()` function.
- `['machine']` section in the `config.yaml`
    - *btn_pin* and *led_pin* to set a visual indication switch *live<->auto* mode
    - *travel_time*\
    the solenoide needs time to reach the bells's contact point. This travel time (named `hit_length` sometimes in the code) is define by the PWM value sended (`message.velocity`).\
    The formula `int((1100*(pow(3.14,(-0.055*p))))+23)` suppose to give the best result where `p` is the `message.velocity` but I failed to implement it correctly because of latency issues.\
    So the travel_time manages a manuel mapping with the `utils.find_index()` and the `travel_time` table in `config.yaml`
- solenoide
    - security setting `max_dronying` exist but i finaly disable it in the exhibition version cause i did not notice too much heat during tests phase of the prototype. In addition sometimes it produces an axe drifting effect that is pretty satisfying and creates some cool patterns wich are not possible with the setting enable and the frequency of hit drasticly improve with `self.d.off`<15ms

